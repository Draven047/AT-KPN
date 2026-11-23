import Foundation
import CoreText

// Register fonts in this test process only; this does not install system fonts.
let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let samplesData = try Data(contentsOf: root.appendingPathComponent("qa/samples.json"))
let samples = try JSONSerialization.jsonObject(with: samplesData) as! [[String:String]]
let fonts = try FileManager.default.contentsOfDirectory(at: root.appendingPathComponent("desktop"), includingPropertiesForKeys: nil).filter { $0.pathExtension == "ttf" }.sorted { $0.path < $1.path }
var results: [[String:Any]] = []
for url in fonts {
    let name = url.deletingPathExtension().lastPathComponent
    var error: Unmanaged<CFError>?
    let registered = CTFontManagerRegisterFontsForURL(url as CFURL, .process, &error)
    let font = CTFontCreateWithName(name as CFString, 48, nil)
    let actualName = CTFontCopyPostScriptName(font) as String
    var cases: [[String:Any]] = []
    for row in samples {
        for key in ["title", "text", "clusters"] {
            let text = row[key]!
            let attributes: [NSAttributedString.Key:Any] = [
                NSAttributedString.Key(kCTFontAttributeName as String): font,
                NSAttributedString.Key(kCTLanguageAttributeName as String): row["lang"]!
            ]
            let line = CTLineCreateWithAttributedString(NSAttributedString(string:text, attributes:attributes))
            let runs = CTLineGetGlyphRuns(line) as! [CTRun]
            var usedFonts: Set<String> = []
            var missing = 0
            for run in runs {
                let attrs = CTRunGetAttributes(run) as NSDictionary
                if let runFont = attrs[kCTFontAttributeName] {
                    usedFonts.insert(CTFontCopyPostScriptName(runFont as! CTFont) as String)
                }
                let count = CTRunGetGlyphCount(run)
                var glyphs = [CGGlyph](repeating:0,count:count)
                CTRunGetGlyphs(run,CFRange(location:0,length:0),&glyphs)
                missing += glyphs.filter { $0 == 0 }.count
            }
            cases.append(["language":row["language"]!,"sample":key,"missing_glyphs":missing,"used_fonts":usedFonts.sorted(),"pass":missing==0 && usedFonts == Set([name])])
        }
    }
    let passed = registered && actualName == name && cases.allSatisfy { $0["pass"] as! Bool }
    results.append(["file":url.lastPathComponent,"registered":registered,"resolved_postscript_name":actualName,"pass":passed,"cases":cases])
    print("\(name): \(passed ? "PASS" : "FAIL") (\(cases.count) CoreText cases)")
}
let payload: [String:Any] = ["engine":"macOS CoreText","registration_scope":"process only","pass":results.allSatisfy { $0["pass"] as! Bool },"fonts":results]
let output = try JSONSerialization.data(withJSONObject:payload, options:[.prettyPrinted,.sortedKeys])
try output.write(to:root.appendingPathComponent("qa/coretext.json"))
if !(payload["pass"] as! Bool) { exit(1) }
