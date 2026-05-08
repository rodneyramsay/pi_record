#!/usr/bin/env python3
import argparse
import re
import shutil
from collections import defaultdict
from pathlib import Path


NEW_TRACKS_DIR = Path.cwd()
VINYL_ROOT_DIR = Path(r"z:\Music\Vinyl")
AUDIO_EXTENSIONS = {".wav", ".flac", ".aiff", ".aif", ".mp3", ".m4a"}
TRACK_SUFFIX_RE = re.compile(r"_[a-z]\d{2}$", re.IGNORECASE)


def normalize_track_name(path):
    return path.stem.casefold()


def album_name_from_track(path):
    return TRACK_SUFFIX_RE.sub("", path.stem)


def normalize_directory_name(path):
    return path.name.casefold()


def iter_audio_files(root):
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.casefold() in AUDIO_EXTENSIONS:
            yield path


def is_empty_directory(path):
    return path.is_dir() and not any(path.iterdir())


def build_old_track_index(vinyl_root):
    index = defaultdict(list)
    print(f"Scanning old vinyl collection: {vinyl_root}")

    for old_track in iter_audio_files(vinyl_root):
        index[normalize_track_name(old_track)].append(old_track)

    print(f"Indexed {sum(len(paths) for paths in index.values())} old audio files")
    return index


def build_empty_album_directory_index(vinyl_root):
    index = defaultdict(list)
    print(f"Scanning empty album directories: {vinyl_root}")

    for directory in vinyl_root.rglob("*"):
        if is_empty_directory(directory):
            index[normalize_directory_name(directory)].append(directory)

    print(f"Indexed {sum(len(paths) for paths in index.values())} empty album directories")
    return index


def choose_destination(new_track, old_matches):
    same_extension_matches = [path for path in old_matches if path.suffix.casefold() == new_track.suffix.casefold()]
    selected_old_track = same_extension_matches[0] if same_extension_matches else old_matches[0]
    return selected_old_track.parent / new_track.name, selected_old_track


def choose_empty_album_destination(new_track, empty_album_directory_index):
    album_name = album_name_from_track(new_track).casefold()
    matches = empty_album_directory_index.get(album_name, [])

    if not matches:
        return None, []

    if len(matches) > 1:
        return None, matches

    return matches[0] / new_track.name, matches


def move_new_tracks(dry_run):
    if not NEW_TRACKS_DIR.exists():
        raise FileNotFoundError(f"New tracks directory does not exist: {NEW_TRACKS_DIR}")

    if not VINYL_ROOT_DIR.exists():
        raise FileNotFoundError(f"Vinyl collection directory does not exist: {VINYL_ROOT_DIR}")

    old_track_index = build_old_track_index(VINYL_ROOT_DIR)
    empty_album_directory_index = build_empty_album_directory_index(VINYL_ROOT_DIR)
    new_tracks = sorted(iter_audio_files(NEW_TRACKS_DIR))

    print(f"Scanning new tracks: {NEW_TRACKS_DIR}")
    print(f"Found {len(new_tracks)} new audio files")
    print(f"Mode: {'dry run, no files will be moved' if dry_run else 'move files'}")

    moved_count = 0
    skipped_count = 0
    missing_count = 0
    ambiguous_count = 0

    for new_track in new_tracks:
        key = normalize_track_name(new_track)
        old_matches = old_track_index.get(key, [])

        print()
        print(f"New track: {new_track}")

        if not old_matches:
            destination, empty_album_matches = choose_empty_album_destination(new_track, empty_album_directory_index)

            if not empty_album_matches:
                print("  No matching old track or empty album directory found; skipping")
                missing_count += 1
                continue

            if destination is None:
                ambiguous_count += 1
                print(f"  Found {len(empty_album_matches)} matching empty album directories; skipping")
                for empty_album_match in empty_album_matches:
                    print(f"    Match: {empty_album_match}")
                continue

            print(f"  No matching old track found")
            print(f"  Using empty album directory: {destination.parent}")
        else:
            if len(old_matches) > 1:
                ambiguous_count += 1
                print(f"  Found {len(old_matches)} matching old tracks")
                for old_match in old_matches:
                    print(f"    Match: {old_match}")

            destination, selected_old_track = choose_destination(new_track, old_matches)
            print(f"  Using old location: {selected_old_track}")
        print(f"  Destination: {destination}")

        if destination.exists():
            print("  Destination already exists; skipping")
            skipped_count += 1
            continue

        if dry_run:
            print(f"  Would move: {new_track} -> {destination}")
            moved_count += 1
            continue

        print(f"  Moving: {new_track} -> {destination}")
        shutil.move(str(new_track), str(destination))
        moved_count += 1

    print()
    print("Summary")
    print(f"  Ready/moved: {moved_count}")
    print(f"  Skipped existing destinations: {skipped_count}")
    print(f"  Missing old locations: {missing_count}")
    print(f"  Ambiguous matches: {ambiguous_count}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Move newly tracked recordings into matching locations under the vinyl collection."
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Print what would be moved without moving any files.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    move_new_tracks(args.dry_run)


if __name__ == "__main__":
    main()
