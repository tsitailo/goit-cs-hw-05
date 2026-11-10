import argparse
import asyncio
import logging
from pathlib import Path
import shutil

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def copy_file(file_path: Path, output_folder: Path) -> None:
    """
    Copies a file to a subfolder in output_folder based on its extension.

    :param file_path: Path of the source file.
    :param output_folder: Path of the destination directory.
    """
    try:

        # Get extension without leading dot, default to 'no_extension' if absent
        extension = file_path.suffix.lstrip(".").lower()
        if not extension:
            extension = "no_extension"

        target_dir = output_folder / extension
        await asyncio.to_thread(target_dir.mkdir, parents=True, exist_ok=True)

        target_file = target_dir / file_path.name
        await asyncio.to_thread(shutil.copyfile, file_path, target_file)

        logging.debug("Successfully copied '%s' -> '%s'", file_path, target_file)

    except Exception as error:
        logging.error("Error copying file '%s': %s", file_path, error)


async def read_folder(source_folder: Path, output_folder: Path) -> None:
    """
    Recursively reads all files in source_folder and schedules copying.

    :param source_folder: Path of the directory to read.
    :param output_folder: Path of the destination directory.
    """
    try:
        items = await asyncio.to_thread(lambda: list(source_folder.iterdir()))
        tasks = []

        for item in items:
            if await asyncio.to_thread(item.is_dir):
                tasks.append(read_folder(item, output_folder))
            elif await asyncio.to_thread(item.is_file):
                tasks.append(copy_file(item, output_folder))

        if tasks:
            await asyncio.gather(*tasks)

    except Exception as error:
        logging.error("Error reading folder '%s': %s", source_folder, error)


async def main() -> None:
    """
    Parses CLI arguments and initiates asynchronous file sorting.
    """
    parser = argparse.ArgumentParser(
        description="Asynchronously sort files into subfolders based on extension."
    )
    parser.add_argument(
        "-s",
        "--source",
        type=str,
        required=True,
        help="Path to the source directory",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Path to the destination directory",
    )

    args = parser.parse_args()

    source_path = Path(args.source)
    output_path = Path(args.output)

    if not await asyncio.to_thread(source_path.exists):
        logging.error("Source directory '%s' does not exist.", source_path)
        return

    if not await asyncio.to_thread(source_path.is_dir):
        logging.error("Source path '%s' is not a directory.", source_path)
        return

    await read_folder(source_path, output_path)
    logging.info("File sorting completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
