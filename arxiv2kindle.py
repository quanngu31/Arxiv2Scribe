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
import typer
import wget

# from getpass import getpass

# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.application import MIMEApplication


class Arxiv2KindleConverter:
    def __init__(self, arxiv_url: str):
        self.arxiv_url = arxiv_url
        self.arxiv_id = re.match(r"((http|https)://.*?/)?(?P<id>\d{4}\.\d{4,5}(v\d{1,2})?)", self.arxiv_url).group("id")
        self.check_prerequisite()

    def check_prerequisite(self):
        result = subprocess.run(["latexmk", "-version"], stdout=None, stderr=None)
        if result.returncode != 0:
            raise SystemError("System does not have latexmk")

    def download_source(self) -> (str, str):
        arxiv_abs = f"https://arxiv.org/abs/{self.arxiv_id}"
        arxiv_pgtitle = html.fromstring(
            requests.get(arxiv_abs).text.encode("utf8")
        ).xpath("/html/head/title/text()")[0]
        arxiv_title = re.sub(r"\s+", " ", re.sub(r"^\[[^]]+\]\s*", "", arxiv_pgtitle))

        tar_filename = Path.cwd() / (arxiv_title + ".tar.gz")
        if not tar_filename.exists():
            arxiv_latex_src_url = f"https://arxiv.org/src/{self.arxiv_id}"
            wget.download(arxiv_latex_src_url, out=str(tar_filename))
            if not tar_filename.exists():
                raise SystemError("Paper Latex source not available")
        return arxiv_title, str(tar_filename)

    def process_tex(self, arxiv_dir, width, height, margin):
        all_texfiles = [str(p) for p in Path(arxiv_dir).rglob("*.tex")]
        kindle_scribe_geometry = f"\\usepackage[papersize={{{width}in,{height}in}}, margin={margin}in]{{geometry}}\n"

        # find files that already have a \usepackage{geometry} declaration
        geometry_files = []
        for texfile in all_texfiles:
            with open(texfile, "r") as f:
                content = f.read()
            if re.search(r"\\usepackage(\[.*?\])?\{geometry\}", content):
                geometry_files.append((texfile, content))

        if len(geometry_files) > 1:
            raise RuntimeError(
                f"Found \\usepackage{{geometry}} in multiple files: {[f for f, _ in geometry_files]}"
            )
        elif len(geometry_files) == 1:
            target_file, content = geometry_files[0]
            print(f"Overwriting geometry in {target_file}", file=sys.stderr)
            new_content = re.sub(
                r"\\usepackage(\[.*?\])?\{geometry\}",
                lambda _: kindle_scribe_geometry.rstrip("\n"),
                content,
            )
            os.rename(target_file, target_file + ".bak")
            with open(target_file, "w") as f:
                f.write(new_content)
            main_texfile = target_file
        else:
            # fallback: find the main .tex file by \documentclass and inject geometry
            main_texfile = None
            for texfile in all_texfiles:
                with open(texfile, "r") as f:
                    content = f.read()
                if r"\documentclass" in content:
                    main_texfile = texfile
                    print(f"Main file is {main_texfile}", file=sys.stderr)
                    break
            if main_texfile is None:
                raise FileNotFoundError("Could not find main .tex file")

            with open(main_texfile, "r") as f:
                src = f.readlines()

            for i, line in enumerate(src):
                if line.startswith(r"\begin{document}"):
                    src.insert(i, kindle_scribe_geometry)
                    break

            os.rename(main_texfile, main_texfile + ".bak")
            with open(main_texfile, "w") as f:
                f.writelines(src)

        subprocess.run(
            ["latexmk", "-f", "-pdf", main_texfile],
            stdout=sys.stderr,
            cwd=Path(main_texfile).parent,
        )
        return main_texfile.removesuffix(".tex") + ".pdf"

    def execute_pipeline(self, width: float, height: float, margin: float):
        arxiv_title, tar_filename = self.download_source()
        print(f"\nArxiv Title: {arxiv_title}")

        with tempfile.TemporaryDirectory(prefix="temp_arxiv2kindle_") as arxiv_dir:
            with tarfile.open(tar_filename) as f:
                f.extractall(arxiv_dir, filter="data")
            pdf_file = self.process_tex(arxiv_dir, width, height, margin)
            safe_title = re.sub(r"[^\w\s\-.]", "_", arxiv_title).strip()
            output_pdf = Path.cwd() / f"{safe_title}.pdf"
            shutil.copy(pdf_file, output_pdf)
            print(f"PDF File for Kindle: {output_pdf}")


    # def send_email(self, pdf_file, arxiv_id, arxiv_title, gmail, kindle_mail):
    #     msg = MIMEMultipart()
    #     pdf_part = MIMEApplication(open(pdf_file, 'rb').read(), _subtype='pdf')
    #     pdf_part.add_header(
    #         'Content-Disposition', 'attachment',
    #         filename=arxiv_id+"_" + arxiv_title + ".pdf")
    #     msg.attach(pdf_part)
    #     server = smtplib.SMTP('smtp.gmail.com', 587)
    #     server.starttls()
    #     gmail_password = getpass(prompt='Enter Gmail Password: ')
    #     server.login(gmail, gmail_password)
    #     server.sendmail(gmail, kindle_mail, msg.as_string())
    #     server.close()


app = typer.Typer()


@app.command()
def main(
    arxiv_url: str = typer.Option(..., "--arxiv-url", "-u", help="arXiv paper URL"),
    width: float = typer.Option(5.25, "--width", "-w", help="Paper width in inches"),
    height: float = typer.Option(7, "--height", "-h", help="Paper height in inches"),
    margin: float = typer.Option(0.45, "--margin", "-m", help="Margin in inches (0.0 - 1.0)"),
    gmail: Optional[str] = typer.Option(
        None, "--gmail", "-g", help="Gmail address for sending to Kindle"
    ),
    kindle_mail: Optional[str] = typer.Option(
        None, "--kindle-mail", "-k", help="Kindle email address"
    ),
):
    if not (0.0 < margin < 1.0):
        raise typer.BadParameter("must be between 0 and 1", param_hint="'--margin'")

    converter = Arxiv2KindleConverter(arxiv_url)
    converter.execute_pipeline(width, height, margin)

    # if gmail is not None and kindle_mail is not None:
    #     typer.echo("Sending Email...")
    #     converter.send_email(pdf_file, arxiv_id, arxiv_title, gmail, kindle_mail)
    #     typer.echo("Done")


if __name__ == "__main__":
    app()
