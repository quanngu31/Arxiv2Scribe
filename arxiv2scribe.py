import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Optional

import lxml.html as html
import requests
import wget

import typer
from rich import print

# from getpass import getpass
# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.application import MIMEApplication


class Arxiv2KindleConverter:
    def __init__(self, arxiv_url: str):
        self.arxiv_url = arxiv_url
        self.arxiv_id = re.match(
            r"((http|https)://.*?/)?(?P<id>\d{4}\.\d{4,5}(v\d{1,2})?)", self.arxiv_url
        ).group("id")
        print(f"> Extracted arxiv ID is {self.arxiv_id}")
        self.arxiv_title = None
        self.check_prerequisite()

    def check_prerequisite(self):
        result = subprocess.run(["latexmk", "-version"], stdout=None, stderr=None)
        if result.returncode != 0:
            raise SystemError("System does not have latexmk")

    # returns the tar file of the latex downloaded if succeeds
    def download_source(self) -> str:
        arxiv_abs_url = f"https://arxiv.org/abs/{self.arxiv_id}"
        arxiv_pgtitle = html.fromstring(
            requests.get(arxiv_abs_url).text.encode("utf8")
        ).xpath("/html/head/title/text()")[0]
        arxiv_title = re.sub(r"\s+", " ", re.sub(r"^\[[^]]+\]\s*", "", arxiv_pgtitle))
        self.arxiv_title = arxiv_title
        print(f"\n> Arxiv Title: {arxiv_title}")

        tar_filename = Path.cwd() / (self.arxiv_id + ".tar.gz")
        if not tar_filename.exists():
            arxiv_latex_src_url = f"https://arxiv.org/src/{self.arxiv_id}"
            wget.download(arxiv_latex_src_url, out=str(tar_filename))
            if not tar_filename.exists():
                raise SystemError("Paper Latex source not available")
        return str(tar_filename)

    # returns the name of the PDF compiled after applying geometry options
    def process_tex(self, arxiv_dir, width, height, margin):
        kindle_scribe_geometry = f"\\usepackage[papersize={{{width}in,{height}in}}, margin={margin}in]{{geometry}}\n"

        # find the main .tex file (the one with \documentclass) for compilation
        main_texfile = None
        tex_contents: dict[str, str] = {}
        for path in Path(arxiv_dir).rglob("*"):
            if not path.is_file():
                continue
            try:
                content = path.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            texfile = str(path)
            tex_contents[texfile] = content
            if main_texfile is None and path.suffix == ".tex" and r"\documentclass" in content:
                main_texfile = texfile
        if main_texfile is None:
            raise FileNotFoundError("Could not find main .tex file")
        print(f"> Main file is {main_texfile}")

        # Find files that already have a \usepackage{geometry} declaration (may differ from main)
        geometry_files = [
            f
            for f, c in tex_contents.items()
            if re.search(r"\\usepackage(\[.*?\])?\{geometry\}", c)
        ]

        if len(geometry_files) > 1:
            raise RuntimeError(
                f"Found \\usepackage{{geometry}} in multiple files: {geometry_files}"
            )
        elif len(geometry_files) == 1:
            target_file = geometry_files[0]
            print(f"> Overwriting geometry in {target_file}")
            new_content = re.sub(
                r"\\usepackage(\[.*?\])?\{geometry\}",
                lambda _: kindle_scribe_geometry.rstrip("\n"),
                tex_contents[target_file],
            )
            os.rename(target_file, target_file + ".bak")
            with open(target_file, "w") as f:
                f.write(new_content)
        else:
            # No geometry package found
            # inject geometry before \begin{document} in the main file
            src = tex_contents[main_texfile].splitlines(keepends=True)
            for i, line in enumerate(src):
                if line.startswith(r"\begin{document}"):
                    src.insert(i, kindle_scribe_geometry)
                    break
            os.rename(main_texfile, main_texfile + ".bak")
            with open(main_texfile, "w") as f:
                f.writelines(src)

        subprocess.run(
            ["latexmk", "-silent", "-f", "-pdf", main_texfile],
            stdout=sys.stderr,
            cwd=Path(main_texfile).parent,
        )
        return main_texfile.removesuffix(".tex") + ".pdf"

    def execute_pipeline(self, width: float, height: float, margin: float, output: Optional[Path] = None):
        tar_src = self.download_source()

        with tempfile.TemporaryDirectory(prefix="temp_arxiv2scribe_") as arxiv_dir:
            with tarfile.open(tar_src) as f:
                f.extractall(arxiv_dir, filter="data")
            pdf_file = self.process_tex(arxiv_dir, width, height, margin)
            if output is not None:
                output_pdf = output
            else:
                safe_title = re.sub(r"[^\w\s\-.]", "_", self.arxiv_title).strip()[:16]
                output_pdf = Path.cwd() / f"{self.arxiv_id}_{safe_title}.pdf"
            shutil.copy(pdf_file, output_pdf)
            print(f"> PDF File for Kindle: {output_pdf}")


app = typer.Typer()


@app.command()
def main(
    arxiv_url: str = typer.Option(..., "--arxiv-url", "-u", help="arXiv URL"),
    width: float = typer.Option(5.25, "--width", "-w", help="Paper width in inches"),
    height: float = typer.Option(7, "--height", "-h", help="Paper height in inches"),
    margin: float = typer.Option(0.50, "--margin", "-m", help="Margin in inches"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output PDF path"),
):
    if not (0.0 < margin < 1.0):
        raise typer.BadParameter("must be between 0 and 1", param_hint="'--margin'")

    converter = Arxiv2KindleConverter(arxiv_url)
    converter.execute_pipeline(width, height, margin, output)


if __name__ == "__main__":
    app()
