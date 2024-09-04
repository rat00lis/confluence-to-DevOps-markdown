# Confluence to Markdown DevOps converter.

Convert Confluence HTML export to Markdown that meets the DevOps wiki format.


## Requirements

You must have [pandoc] command line tool installed. Check it by running:

```
pandoc --version
```

Install all project dependencies:

```
npm install
```


## Usage

In the converter's directory:

```
npm run start <pathResource> <pathResult>
```


### Parameters

parameter | description
--- | ---
`<pathResource>` | File or directory to convert with extracted Confluence export
`<pathResult>` | Directory to where the output will be generated to. Defaults to current working directory


## Original process description
For the original description, including areas for improvement and limitations, please refer to the original repository from which this one is forked.


### Export to HTML

Note that if the converter does not know how to handle a style, HTML to Markdown typically just leaves the HTML untouched (Markdown does allow for HTML tags).


## Step by step guide for Confluence data export<a name="conflhowto"></a>

1. Go to the space and choose `Space tools > Content Tools on the sidebar`.
    - If you are in an older version of Confluence, this option might be on the top of the space under Browser > Space Operations 
2. Choose Export. This option will only be visible if you have the **Export Space** permission.
3. Select HTML then choose Next.
4. Decide whether you need to customize the export:
  - Select Normal Export to produce an HTML file containing all the pages that you have permission to view.
  - Select Custom Export if you want to export a subset of pages, or to exclude comments from the export.
5. Extract zip

## Step by step guide for converting html files to DevOps wiki mardown
1. For all spaces to migrate.
    1.1. Run the script with the extracted html export folder as a parameter, as well as the output path.
    ```
    npm run start <pathResource> <pathResult>
    ```
    1.2. Once the convertion is done, use the *devops_organizer.py* script. This will create a new folder with all the files reorganized and re-linked based on their supossed path. 
      - Make sure the order of the paths is correct.
      - Also, make sure to use the folder **inside** of the output folder, since that is the one with all the markdown files for the convertion.
    ```
    py devops_organizer.py <output_path> <folder_path>
    ``` 
    1.3. To add the original dates of creation and authors, use the *dates_includer.py* script, that will add a line of text at the end of all files including their original creation.
      - For this, you will need to provide:
        - The original **HTML** folder with all the htmls files inside.
        - The converted **MD** folder created in the previous step.
        - An output directory.
    ```
    py dates_includer.py <html_folder> <md_folder> <output_folder>
    ```
2. Open the root directory for the migrated spaces (the directory that contains all the exported folders) and make sure the links are working properly.
3. Submit your project into a DevOps repository.
4. Go to Overview > Wiki > Options (dots in the top of the table of content) and Publish your code as wiki.
5. Your confluence space was succesfully migrated to DevOps wiki :)


[pandoc]: http://pandoc.org/installing.html
