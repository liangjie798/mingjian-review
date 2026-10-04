using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Spreadsheet;
using DocumentFormat.OpenXml.Wordprocessing;
using System.IO.Compression;
using System.Text;
using UglyToad.PdfPig;

namespace MingJian.Desktop.Services;

public static class DocumentParser
{
    public static readonly HashSet<string> Supported = new(StringComparer.OrdinalIgnoreCase)
        { ".pdf", ".docx", ".xlsx", ".txt", ".md", ".csv", ".json", ".zip" };

    private static readonly HashSet<string> SupportedArchiveEntries = new(Supported.Where(x => x != ".zip"), StringComparer.OrdinalIgnoreCase);
    private const int MaxArchiveEntries = 300;
    private const long MaxArchiveBytes = 250L * 1024 * 1024;
    private const long MaxEntryBytes = 60L * 1024 * 1024;

    public static Task<ParsedDocument> ParseAsync(string path) => Task.Run(() => Parse(path));
    public static Task<IReadOnlyList<ParsedDocument>> ParseManyAsync(string path) => Task.Run(() => ParseMany(path));

    public static IReadOnlyList<ParsedDocument> ParseMany(string path) =>
        Path.GetExtension(path).Equals(".zip", StringComparison.OrdinalIgnoreCase) ? ParseZip(path) : [Parse(path)];

    public static ParsedDocument Parse(string path)
    {
        var extension = Path.GetExtension(path).ToLowerInvariant();
        return extension switch
        {
            ".pdf" => ParsePdf(path),
            ".docx" => ParseDocx(path),
            ".xlsx" => ParseXlsx(path),
            ".txt" or ".md" or ".csv" or ".json" => new(Path.GetFileName(path), [File.ReadAllText(path)], "文本解析"),
            ".zip" => ParseZip(path)[0],
            _ => throw new NotSupportedException($"暂不支持 {extension} 格式")
        };
    }

    private static IReadOnlyList<ParsedDocument> ParseZip(string path)
    {
        var archiveName = Path.GetFileName(path);
        var documents = new List<ParsedDocument>();
        var inventory = new List<string>();
        var unsafeEntries = 0;
        var unsupportedEntries = 0;
        var supportedEntries = 0;
        long totalBytes = 0;
        var tempFolder = Path.Combine(Path.GetTempPath(), "MingJian", "zip-" + Guid.NewGuid().ToString("N"));

        try
        {
            using var archive = ZipFile.OpenRead(path);
            var files = archive.Entries.Where(x => !string.IsNullOrEmpty(x.Name)).ToArray();
            if (files.Length > MaxArchiveEntries)
                throw new InvalidDataException($"压缩包包含 {files.Length} 个文件，超过 {MaxArchiveEntries} 个文件的安全上限。");

            Directory.CreateDirectory(tempFolder);
            for (var index = 0; index < files.Length; index++)
            {
                var entry = files[index];
                var entryName = entry.FullName.Replace('\\', '/');
                if (IsUnsafeArchivePath(entryName))
                {
                    unsafeEntries++;
                    inventory.Add("[危险路径已跳过]");
                    continue;
                }

                inventory.Add(entryName);
                if (entry.Length > MaxEntryBytes)
                    throw new InvalidDataException($"压缩包内文件“{entryName}”超过 60 MB 的安全上限。");
                totalBytes += entry.Length;
                if (totalBytes > MaxArchiveBytes)
                    throw new InvalidDataException("压缩包解压后的总体积超过 250 MB 的安全上限。");
                if (entry.Length > 1024 * 1024 && entry.CompressedLength > 0 && entry.Length / (double)entry.CompressedLength > 500)
                    throw new InvalidDataException($"压缩包内文件“{entryName}”的压缩率异常，已停止解析。");

                var extension = Path.GetExtension(entryName);
                if (!SupportedArchiveEntries.Contains(extension))
                {
                    unsupportedEntries++;
                    continue;
                }

                supportedEntries++;
                var tempPath = Path.Combine(tempFolder, $"{index:D4}{extension.ToLowerInvariant()}");
                using (var source = entry.Open())
                using (var destination = File.Create(tempPath))
                    source.CopyTo(destination);
                var parsed = Parse(tempPath);
                documents.Add(parsed with { Name = $"{archiveName} / {entryName}" });
            }

            var summaryLines = new List<string>
            {
                $"ZIP_ARCHIVE={archiveName}",
                $"ZIP_ENTRY_COUNT={files.Length}",
                $"ZIP_SUPPORTED_COUNT={supportedEntries}",
                $"ZIP_UNSUPPORTED_COUNT={unsupportedEntries}",
                $"ZIP_UNSAFE_COUNT={unsafeEntries}",
                "ZIP_FILE_LIST:"
            };
            summaryLines.AddRange(inventory);
            var summary = string.Join('\n', summaryLines);
            documents.Insert(0, new ParsedDocument(archiveName, [summary], "ZIP 清单"));
            return documents;
        }
        catch (InvalidDataException error) when (!error.Message.StartsWith("压缩包", StringComparison.Ordinal))
        {
            throw new InvalidDataException("ZIP 文件已损坏或格式无效，无法读取。", error);
        }
        finally
        {
            if (Directory.Exists(tempFolder)) Directory.Delete(tempFolder, true);
        }
    }

    private static bool IsUnsafeArchivePath(string path) =>
        path.StartsWith('/') || path.Contains("../", StringComparison.Ordinal) || path.Contains(':');

    private static ParsedDocument ParsePdf(string path)
    {
        using var pdf = PdfDocument.Open(path);
        var pages = pdf.GetPages().Select(p => p.Text).ToArray();
        return new(Path.GetFileName(path), pages, "PdfPig");
    }

    private static ParsedDocument ParseDocx(string path)
    {
        using var doc = WordprocessingDocument.Open(path, false);
        var body = doc.MainDocumentPart?.Document.Body;
        var lines = body?.Descendants<Paragraph>()
            .Select(p => string.Concat(p.Descendants<DocumentFormat.OpenXml.Wordprocessing.Text>().Select(t => t.Text)))
            .Where(x => !string.IsNullOrWhiteSpace(x)) ?? [];
        return new(Path.GetFileName(path), [string.Join(Environment.NewLine, lines)], "Open XML");
    }

    private static ParsedDocument ParseXlsx(string path)
    {
        using var doc = SpreadsheetDocument.Open(path, false);
        var workbook = doc.WorkbookPart ?? throw new InvalidDataException("工作簿结构无效");
        var shared = workbook.SharedStringTablePart?.SharedStringTable?.Elements<SharedStringItem>()
            .Select(x => x.InnerText).ToArray() ?? [];
        var pages = new List<string>();
        foreach (var sheet in workbook.Workbook.Sheets!.Elements<Sheet>())
        {
            var part = (WorksheetPart)workbook.GetPartById(sheet.Id!);
            var builder = new StringBuilder($"工作表：{sheet.Name}\n");
            foreach (var row in part.Worksheet.Descendants<Row>())
            {
                var values = row.Elements<Cell>().Select(cell => CellValue(cell, shared));
                builder.AppendLine(string.Join(" | ", values));
            }
            pages.Add(builder.ToString());
        }
        return new(Path.GetFileName(path), pages.ToArray(), "Open XML");
    }

    private static string CellValue(Cell cell, string[] shared)
    {
        var raw = cell.CellValue?.Text ?? cell.InnerText;
        if (cell.DataType?.Value == CellValues.SharedString && int.TryParse(raw, out var index) && index < shared.Length)
            return shared[index];
        return raw;
    }
}
