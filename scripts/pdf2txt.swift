import PDFKit
import Foundation
let a = CommandLine.arguments
let doc = PDFDocument(url: URL(fileURLWithPath: a[1]))!
try! (doc.string ?? "").write(toFile: a[2], atomically: true, encoding: .utf8)
