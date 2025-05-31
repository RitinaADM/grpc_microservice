

#!/usr/bin/env python3

import os
from typing import Optional

# Списки исключений
EXCLUDED_DIRS = {
    ".venv",        # Виртуальная среда
    "__pycache__",  # Кэш Python
    ".git",         # Репозиторий Git
    ".idea",
    ".pytest_cache",
    #"proto"
}

EXCLUDED_FILES = {
    "project_contents.txt",
    ".gitignore",
    "*.pyc",
    "*.log",
    "readme.md",
    "p_t.py",
    "gen_jwt.py",
    "coverage.xml",
    "service_pb2.py",
    "service_pb2_grpc",
}

def should_exclude(path: str, excluded_dirs: set, excluded_files: set) -> bool:
    """
    Проверяет, нужно ли исключить файл или директорию из обработки.
    """
    from fnmatch import fnmatch

    base_name = os.path.basename(os.path.normpath(path))

    if base_name in excluded_dirs:
        print(f"Исключена директория: {path}")
        return True

    for pattern in excluded_files:
        if fnmatch(base_name, pattern):
            print(f"Исключен файл: {path}")
            return True

    return False

def collect_project_contents(directory: str, output_file: str = "project_contents.txt") -> None:
    """
    Собирает содержимое всех текстовых файлов в указанной директории и записывает их в один файл.
    """
    try:
        if not os.path.isdir(directory):
            raise ValueError(f"Директория '{directory}' не существует или не является директорией")

        print(f"Сбор содержимого из директории: {directory}")
        included_files = 0

        with open(output_file, "w", encoding="utf-8") as out_file:
            out_file.write(f"# Содержимое проекта из директории: {directory}\n\n")

            for root, dirs, files in os.walk(directory):
                dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d), EXCLUDED_DIRS, EXCLUDED_FILES)]

                if not files:
                    print(f"Нет файлов в директории: {root}")

                for file in sorted(files):
                    file_path = os.path.join(root, file)
                    if should_exclude(file_path, EXCLUDED_DIRS, EXCLUDED_FILES):
                        continue

                    relative_path = os.path.relpath(file_path, directory)
                    print(f"Добавлен файл: {relative_path}")
                    included_files += 1

                    out_file.write(f"## Файл: {relative_path}\n")
                    out_file.write("```text\n")

                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if not content.strip():
                                out_file.write("[Файл пуст]")
                            else:
                                out_file.write(content)
                                print(f"Записано содержимое файла: {relative_path} ({len(content)} символов)")
                    except UnicodeDecodeError:
                        out_file.write("[Содержимое файла не является текстом или закодировано не в UTF-8]")
                        print(f"Не удалось прочитать как текст: {relative_path}")
                    except PermissionError:
                        out_file.write("[Нет доступа к файлу]")
                        print(f"Нет доступа: {relative_path}")
                    except Exception as e:
                        out_file.write(f"[Ошибка при чтении файла: {str(e)}]")
                        print(f"Ошибка чтения: {relative_path} - {str(e)}")

                    out_file.write("\n```\n\n")

            out_file.flush()  # Сбрасываем буфер

        if included_files == 0:
            print("Ни один файл не был добавлен в итоговый файл. Проверьте исключения или структуру проекта.")
        else:
            print(f"Добавлено файлов: {included_files}")
        print(f"Содержимое проекта успешно сохранено в '{output_file}'")

        # Проверяем размер файла
        file_size = os.path.getsize(output_file)
        print(f"Размер итогового файла: {file_size} байт")
        if file_size == 0:
            print("Итоговый файл пуст! Проверьте логи выше.")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")

def main() -> None:
    """
    Точка входа для запуска скрипта.
    """
    project_dir = os.path.dirname(os.path.abspath(__file__))
    collect_project_contents(project_dir)

if __name__ == "__main__":
    main()