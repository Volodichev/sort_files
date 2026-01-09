# sort_files


> **Disclaimer**<a name="disclaimer" />: Please make backup your media before using this script!

Sort files with SUPPORTED_EXTENSIONS by creation date and put them to directories Year/Month/Day by exif headers Date. If there is no exif Date it takes from os creation time. Use PIL, piexif, exifread, pyexiv2 libraries.
Sorting jpeg files by date and time from EXIF.

for ex.:

C:\Users\user\sort_files\result\2017\6\19\IMG_1017.jpg


### Installation Instructions

1. Fork/Clone/Download this repo
    ```elm
    git clone https://github.com/Volodichev/sort_files.git
    ```

2. Navigate to the directory

    ```elm
    cd sort_files`
    ```

3. Install the dependencies

    ```elm
    pip install -r requirements.txt
    ```

4. Put copy of your files to folder 'source'

5. Run the sort_files.py script and all sorted staff will move to folder 'result' 

## GUI (PyQt6)

- Install deps `pip install -r requirements.txt`
- Run `python gui.py`
- In the interface, select the `source` and `result` folders, configure extensions and flags from `config.py`, then click "Start sorting".


