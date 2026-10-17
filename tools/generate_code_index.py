"""
Automated Code Index & Symbol Register Generator for STB Pro Qt6.
Parses the Python AST of all modules, classes, methods, functions, tests, and UI components
to generate an up-to-date, comprehensive, line-exact CODE_INDEX.md for developers and AI agents.
"""
import ast
import os
import sys
from typing import Dict, List, Any, Optional


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SymbolVisitor(ast.NodeVisitor):
    def __init__(self, filename: str, lines: List[str]):
        self.filename = filename
        self.lines = lines
        self.docstring = ""
        self.classes: List[Dict[str, Any]] = []
        self.functions: List[Dict[str, Any]] = []
        self.constants: List[Dict[str, Any]] = []
        self.current_class = None

    def visit_Module(self, node: ast.Module):
        self.docstring = ast.get_docstring(node) or ""
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        class_info = {
            "name": node.name,
            "start_line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "docstring": (ast.get_docstring(node) or "").split("\n")[0].strip(),
            "bases": [ast.unparse(b) for b in node.bases],
            "methods": [],
            "signals": [],
        }
        prev_class = self.current_class
        self.current_class = class_info
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in item.args.args if a.arg != "self"]
                doc = (ast.get_docstring(item) or "").split("\n")[0].strip()
                class_info["methods"].append({
                    "name": item.name,
                    "start_line": item.lineno,
                    "end_line": getattr(item, "end_lineno", item.lineno),
                    "args": ", ".join(args),
                    "docstring": doc,
                    "is_async": isinstance(item, ast.AsyncFunctionDef),
                })
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        val_str = ast.unparse(item.value)
                        if "Signal(" in val_str:
                            class_info["signals"].append({
                                "name": target.id,
                                "line": item.lineno,
                                "val": val_str,
                            })
        self.classes.append(class_info)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self.current_class is None:
            args = [a.arg for a in node.args.args]
            doc = (ast.get_docstring(node) or "").split("\n")[0].strip()
            self.functions.append({
                "name": node.name,
                "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "args": ", ".join(args),
                "docstring": doc,
                "is_async": False,
            })
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        if self.current_class is None:
            args = [a.arg for a in node.args.args]
            doc = (ast.get_docstring(node) or "").split("\n")[0].strip()
            self.functions.append({
                "name": node.name,
                "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "args": ", ".join(args),
                "docstring": doc,
                "is_async": True,
            })
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        if self.current_class is None:
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    self.constants.append({
                        "name": target.id,
                        "line": node.lineno,
                        "val": ast.unparse(node.value)[:60],
                    })
        self.generic_visit(node)


def scan_file(filepath: str) -> Optional[SymbolVisitor]:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        lines = content.splitlines()
        tree = ast.parse(content, filename=filepath)
        visitor = SymbolVisitor(filepath, lines)
        visitor.visit(tree)
        return visitor
    except Exception as e:
        print(f"Warn: Fehler beim Parsen von {filepath}: {e}", file=sys.stderr)
        return None


def generate_index() -> str:
    categories = {
        "Clients (Protokolle & APIs)": "clients",
        "Core (Business Logic, Cache & DB)": "core",
        "Player & Engine (VLC, Proxy & OSD)": "player",
        "UI - Hauptfenster & Theme": "ui",
        "UI - Views & Workspaces": "ui/views",
        "UI - Komponenten & Controls": "ui/components",
        "UI - Dialoge & Overlays": "ui/dialogs",
        "UI - Virtuelle Models & Delegates": "ui/models",
        "Automatisierte Test-Suiten": "tests",
        "Einstiegspunkt": "main.py",
    }

    scanned_data: Dict[str, List[SymbolVisitor]] = {k: [] for k in categories}
    all_symbols = []

    for root, dirs, files in os.walk(ROOT_DIR):
        if ".venv" in root or "__pycache__" in root or ".git" in root or "tools" in root:
            continue
        for file in sorted(files):
            if not file.endswith(".py"):
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, ROOT_DIR).replace("\\", "/")

            vis = scan_file(full_path)
            if not vis:
                continue

            # Zuordnung zu Kategorie
            cat_assigned = False
            for cat_name, cat_prefix in categories.items():
                if cat_prefix.endswith(".py"):
                    if rel_path == cat_prefix:
                        scanned_data[cat_name].append(vis)
                        cat_assigned = True
                        break
                elif rel_path.startswith(cat_prefix + "/") or rel_path == cat_prefix:
                    # Specific subfolder check
                    if "/" in cat_prefix:
                        scanned_data[cat_name].append(vis)
                        cat_assigned = True
                        break
            if not cat_assigned:
                for cat_name, cat_prefix in categories.items():
                    if "/" not in cat_prefix and rel_path.startswith(cat_prefix + "/"):
                        scanned_data[cat_name].append(vis)
                        cat_assigned = True
                        break

            # Collect global symbols for master table
            for cls in vis.classes:
                all_symbols.append({
                    "name": cls["name"],
                    "type": "Class / Widget",
                    "file": rel_path,
                    "line": cls["start_line"],
                    "end_line": cls["end_line"],
                    "doc": cls["docstring"] or f"Basis: {', '.join(cls['bases'])}",
                })
            for fn in vis.functions:
                all_symbols.append({
                    "name": fn["name"],
                    "type": "Function",
                    "file": rel_path,
                    "line": fn["start_line"],
                    "end_line": fn["end_line"],
                    "doc": fn["docstring"] or f"def {fn['name']}({fn['args']})",
                })

    all_symbols.sort(key=lambda s: s["name"].lower())

    # Build Markdown Content
    md = []
    md.append("# 📑 STB Pro Qt6 — Vollständiges Code-Register & Symbol-Index")
    md.append("")
    md.append("> **Wichtig für Entwickler & AI-Agents**: Dieses Register wird automatisiert durch `tools/generate_code_index.py` gepflegt. Bevor Dateien im Repository blind durchsucht werden, immer zuerst diesen Index konsultieren, um Funktionssignaturen, Zeilennummern und Architektur-Zuständigkeiten direkt anzusteuern.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 🧭 Inhaltsverzeichnis")
    md.append("1. [Alphabetisches Master-Symbolverzeichnis](#alphabetisches-master-symbolverzeichnis)")
    for cat_name in categories:
        slug = cat_name.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("&", "").replace("/", "")
        md.append(f"- [{cat_name}](#{slug})")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 🔍 Alphabetisches Master-Symbolverzeichnis")
    md.append("")
    md.append("| Symbol | Typ | Datei | Zeilen | Kurzbeschreibung |")
    md.append("| :--- | :---: | :--- | :---: | :--- |")
    for sym in all_symbols:
        file_link = f"[{sym['file']}]({sym['file']}#L{sym['line']}-L{sym['end_line']})"
        doc_short = (sym['doc'][:90] + "...") if len(sym['doc']) > 90 else sym['doc']
        md.append(f"| `{sym['name']}` | **{sym['type']}** | {file_link} | `L{sym['line']}-L{sym['end_line']}` | {doc_short} |")

    md.append("")
    md.append("---")
    md.append("")

    # Detail Category Sections
    for cat_name, visitors in scanned_data.items():
        if not visitors:
            continue
        slug = cat_name.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("&", "").replace("/", "")
        md.append(f"## 📦 {cat_name}")
        md.append("")
        for vis in visitors:
            rel = os.path.relpath(vis.filename, ROOT_DIR).replace("\\", "/")
            total_lines = len(vis.lines)
            md.append(f"### 📄 [`{rel}`]({rel}) ({total_lines} Zeilen)")
            if vis.docstring:
                md.append(f"> {vis.docstring.strip()}")
                md.append("")

            if vis.classes:
                md.append("#### Klassen & Komponenten")
                for cls in vis.classes:
                    bases_str = f" : *{', '.join(cls['bases'])}*" if cls['bases'] else ""
                    md.append(f"- **[`{cls['name']}`]({rel}#L{cls['start_line']}-L{cls['end_line']})**{bases_str} — `L{cls['start_line']}-L{cls['end_line']}`")
                    if cls['docstring']:
                        md.append(f"  - *{cls['docstring']}*")
                    if cls['signals']:
                        sig_names = ", ".join(f"`{s['name']}`" for s in cls['signals'])
                        md.append(f"  - **Signals**: {sig_names}")
                    if cls['methods']:
                        md.append("  - **Wichtige Methoden:**")
                        for m in cls['methods'][:15]:  # show up to 15 key methods
                            md.append(f"    - [`{m['name']}({m['args']})`]({rel}#L{m['start_line']}) — `L{m['start_line']}`" + (f" *({m['docstring']})*" if m['docstring'] else ""))
                        if len(cls['methods']) > 15:
                            md.append(f"    - *... und {len(cls['methods']) - 15} weitere Hilfsmethoden.*")
                md.append("")

            if vis.functions:
                md.append("#### Modul-Funktionen")
                for fn in vis.functions:
                    md.append(f"- **[`{fn['name']}({fn['args']})`]({rel}#L{fn['start_line']}-L{fn['end_line']})** — `L{fn['start_line']}`" + (f" — *{fn['docstring']}*" if fn['docstring'] else ""))
                md.append("")

            if vis.constants:
                md.append("#### Wichtige Konstanten / Konfigurationen")
                const_list = [f"`{c['name']}` (L{c['line']})" for c in vis.constants[:12]]
                md.append("- " + ", ".join(const_list))
                md.append("")

            md.append("---")
            md.append("")

    return "\n".join(md)


def main():
    check_mode = "--check" in sys.argv
    print(f"Scanning codebase under: {ROOT_DIR} ...")
    content = generate_index()
    out_file = os.path.join(ROOT_DIR, "CODE_INDEX.md")

    if check_mode:
        if not os.path.exists(out_file):
            print("[FAIL] CODE_INDEX.md existiert nicht!")
            sys.exit(1)
        with open(out_file, "r", encoding="utf-8") as f:
            existing = f.read()
        if existing == content:
            print("[OK] CODE_INDEX.md ist aktuell und synchron mit dem Codebase-Stand.")
            sys.exit(0)
        else:
            print("[FAIL] CODE_INDEX.md weicht vom aktuellen Codebase-Stand ab! Bitte 'python tools/generate_code_index.py' ausführen.")
            sys.exit(1)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] CODE_INDEX.md erfolgreich generiert ({len(content)} Bytes, {len(content.splitlines())} Zeilen)!")


if __name__ == "__main__":
    main()
