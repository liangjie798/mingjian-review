using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Spreadsheet;
using DocumentFormat.OpenXml.Wordprocessing;
using System.Text;
using UglyToad.PdfPig;

namespace MingJian.Desktop.Services;

public static class DocumentParser
{
    public static readonly HashSet<string> Supported = new(StringComparer.OrdinalIgnoreCase)
        { ".pdf", ".docx", ".xlsx", ".txt", ".md", ".csv", ".json" };

    public static Task<ParsedDocument> ParseAsync(string path) => Task.Run(() => Parse(path));

    public static ParsedDocument Parse(string path)
    {
        var extension = Path.GetExtension(path).ToLowerInvariant();
        return extension switch
        {
            ".pdf" => ParsePdf(path),
            ".docx" => ParseDocx(path),
            ".xlsx" => ParseXlsx(path),
            ".txt" or ".md" or ".csv" or ".json" => new(Path.GetFileName(path), [File.ReadAllText(path)], "文本解析"),
            _ => throw new NotSupportedException($"暂不支持 {extension} 格式")
        };
    }

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
