param(
    [Parameter(Mandatory=$true)][string]$DocumentPath,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
$acksDocPath = [IO.Path]::GetFullPath($DocumentPath)
$acksOutDir = [IO.Path]::GetFullPath($OutputDirectory)
$acksExpectedRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\ACKSII\Сборки для чтения'))
if (-not $acksDocPath.StartsWith($acksExpectedRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Only the separate reading copy may be opened for authoring.' }
[IO.Directory]::CreateDirectory($acksOutDir) | Out-Null
$acksWord = $null
$acksDocument = $null
try {
    # Create our own invisible Word instance; never attach to user documents.
    $acksWord = New-Object -ComObject Word.Application
    $acksWord.Visible = $false
    $acksWord.DisplayAlerts = 0
    $acksDocument = $acksWord.Documents.Open($acksDocPath, $false, $false)
    $acksDocument.ActiveWindow.View.Type = 3
    $acksDocument.ActiveWindow.View.ShowComments = $true
    $acksDocument.ActiveWindow.View.ShowRevisionsAndComments = $true
    $acksDocument.ActiveWindow.View.RevisionsMode = 0
    $acksDocument.TrackRevisions = $false
    $acksDocument.PrintRevisions = $true
    $acksDocument.Content.LanguageID = 1049
    $acksDocument.Repaginate()
    $acksDocument.Save()
    $acksBodyPdf = Join-Path $acksOutDir 'body.pdf'
    $acksMarkupPdf = Join-Path $acksOutDir 'with_comments.pdf'
    $acksDocument.ExportAsFixedFormat($acksBodyPdf, 17, $false, 0, 0, 1, 1, 0, $true, $true, 1, $true, $true, $false)
    Write-Output 'Body PDF exported from Word.'
    $acksDocument.ExportAsFixedFormat($acksMarkupPdf, 17, $false, 0, 0, 1, 1, 7, $true, $true, 1, $true, $true, $false)
    Write-Output 'PDF with margin comments exported from Word.'
    $acksComments = @()
    foreach ($acksComment in $acksDocument.Comments) {
        $acksComments += [PSCustomObject]@{
            index = $acksComment.Index
            page = $acksComment.Scope.Information(3)
            text = $acksComment.Range.Text
            anchor = $acksComment.Scope.Text
        }
    }
    [PSCustomObject]@{
        document = $acksDocPath
        pages = $acksDocument.ComputeStatistics(2)
        comment_count = $acksDocument.Comments.Count
        comments = $acksComments
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $acksOutDir 'word_render.json') -Encoding utf8
} finally {
    if ($null -ne $acksDocument) {
        $acksDocument.Close(0)
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($acksDocument) | Out-Null
    }
    if ($null -ne $acksWord) {
        $acksWord.Quit(0)
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($acksWord) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
