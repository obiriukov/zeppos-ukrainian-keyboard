#!/usr/bin/env python3
import zipfile
import os
import shutil

ZIP_PATH = "node_modules.zip"
EXTRACT_FOLDER = "node_modules"

def safe_make_dir(path):
    os.makedirs(path, exist_ok=True)

def is_within_directory(directory, target):
    # Захист від zip-slip
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return os.path.commonpath([abs_directory]) == os.path.commonpath([abs_directory, abs_target])

def safe_extract_member(zipf, member, target_path):
    # member: ZipInfo
    member_name = member.filename
    if member.is_dir():
        safe_make_dir(target_path)
        return
    # ensure parent dir exists
    parent = os.path.dirname(target_path)
    if parent:
        safe_make_dir(parent)
    with zipf.open(member, "r") as source, open(target_path, "wb") as dest:
        shutil.copyfileobj(source, dest)

def main():
    if not os.path.isfile(ZIP_PATH):
        print(f"Архів не знайдено: {ZIP_PATH}")
        return

    safe_make_dir(EXTRACT_FOLDER)

    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        names = z.namelist()

        # Перевіримо, чи є в архіві згадки node_modules/
        has_node_modules_paths = any(("node_modules/" in n) or (n.rstrip("/") == "node_modules") for n in names)

        if has_node_modules_paths:
            # Витягуємо лише те, що всередині node_modules, прибираючи префікс до node_modules/
            for member in z.infolist():
                name = member.filename
                # Ігноруємо мета-шляхи на кшталт __MACOSX, але це не обов'язково
                if "node_modules/" in name:
                    # беремо частину після першого входження 'node_modules/'
                    rel = name.split("node_modules/", 1)[1]
                    if not rel:
                        # якщо це сама папка node_modules (директорія), пропускаємо
                        continue
                    dest = os.path.join(EXTRACT_FOLDER, rel)
                elif name.rstrip("/") == "node_modules":
                    # папка node_modules сама по собі — пропускаємо
                    continue
                else:
                    # ігноруємо все, що не всередині node_modules
                    continue

                # захист від виходу за межі папки призначення
                if not is_within_directory(EXTRACT_FOLDER, dest):
                    raise Exception("Виявлено потенційно небезпечний шлях в архіві: " + name)

                # створюємо та записуємо
                if member.is_dir():
                    safe_make_dir(dest)
                else:
                    safe_make_dir(os.path.dirname(dest) or ".")
                    safe_extract_member(z, member, dest)
        else:
            # В архіві немає node_modules — розпакуємо все як є в папку EXTRACT_FOLDER
            for member in z.infolist():
                dest = os.path.join(EXTRACT_FOLDER, member.filename)
                # захист від zip-slip
                if not is_within_directory(EXTRACT_FOLDER, dest):
                    raise Exception("Виявлено потенційно небезпечний шлях в архіві: " + member.filename)
                if member.is_dir():
                    safe_make_dir(dest)
                else:
                    safe_make_dir(os.path.dirname(dest) or ".")
                    safe_extract_member(z, member, dest)

    print(f"Розпакування завершено в папку: {EXTRACT_FOLDER}")

if __name__ == "__main__":
    main()
