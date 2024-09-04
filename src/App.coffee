class App

  # @link http://hackage.haskell.org/package/pandoc For options description
  @outputTypesAdd = [
    'markdown_github' # use GitHub markdown variant
    'blank_before_header' # insert blank line before header
    #'mmd_link_attributes' # use MD syntax for images and links instead of HTML
    #'link_attributes' # use MD syntax for images and links instead of HTML
  ]

  @outputTypesRemove = []

  @extraOptions = [
    '--markdown-headings=atx' # Setext-style headers (underlined) | ATX-style headers (prefixed with hashes)
  ]

  ###*
  # @param {fs} _fs Required lib
  # @param {sync-exec} _exec Required lib
  # @param {path} _path Required lib
  # @param {mkdirp} _mkdirp Required lib
  # @param {Utils} utils My lib
  # @param {Formatter} formatter My lib
  # @param {PageFactory} pageFactory My lib
  # @param {Logger} logger My lib
  ###
  constructor: (@_fs, @_exec, @_path, @_mkdirp, @utils, @formatter, @pageFactory, @logger) ->
    typesAdd = App.outputTypesAdd.join '+'
    typesRemove = App.outputTypesRemove.join '-'
    typesRemove = if typesRemove then '-' + typesRemove else ''
    types = typesAdd + typesRemove
    @pandocOptions = [
      if types then '-t ' + types else ''
      App.extraOptions.join ' '
    ].join ' '

  ###*
  # Converts HTML files to MD files.
  # @param {string} dirIn Directory to go through
  # @param {string} dirOut Directory where to place converted MD files
  ###
  convert: (dirIn, dirOut) ->
    filePaths = @utils.readDirRecursive dirIn
    pages = (@pageFactory.create filePath for filePath in filePaths when filePath.endsWith '.html')

    indexHtmlFiles = []
    for page in pages
      do (page) =>
        if page.fileName == 'index.html'
          indexHtmlFiles.push @_path.join page.space, 'index.md' # gitit requires link to pages without .md extension
        @convertPage page, dirIn, dirOut, pages

    @writeGlobalIndexFile indexHtmlFiles, dirOut if not @utils.isFile dirIn
    @logger.info 'Conversion done'

  ###*
  # Converts HTML file at given path to MD.
  # @param {Page} page Page entity of HTML file
  # @param {string} dirOut Directory where to place converted MD files
  ###
  convertPage: (page, dirIn, dirOut, pages) ->
    @logger.info 'Parsing ... ' + page.path
    breadcrumbs = page.getBreadcrumbs()
    text = page.getTextToConvert pages
    # Remove the specific attachments div
    text = @removeAttachmentsDiv text
      
    fullOutFileName = @_path.join dirOut, page.space, page.fileNameNew

    @logger.info 'Making Markdown ... ' + fullOutFileName
    @writeMarkdownFile text, fullOutFileName, breadcrumbs
    @utils.copyAssets @utils.getDirname(page.path), @utils.getDirname(fullOutFileName)
    @logger.info 'Done\n'

  ###*
  # Removes the attachments div from the HTML content.
  # @param {string} text HTML content of the file
  # @return {string} Modified HTML content without the attachments div
  ###
  removeAttachmentsDiv: (text) ->
    # Regular expression to match the attachments section
    attachmentsRegex = ///
        <div \s class="pageSectionHeader"> \s* 
          <h2 \s id="attachments" \s class="pageSectionTitle">Attachments:<\/h2> \s* 
        <\/div> \s* 
        <div \s class="greybox" \s align="left"> [\s\S]*? 
        <\/div> \s* 
    ///

    # Regular expression to match the JIRA section
    jiraRegex = ///
        <h3 \s id="PayPalExpressCheckout-JIRA">JIRA<\/h3> \s* 
        <p> \s* 
          <a \s href="https:\/\/tracker\/browse\/AVT-8209" \s class \s rel="nofollow">https:\/\/tracker\/browse\/AVT-8209<\/a> \s* 
        <\/p> \s* 
    ///

    # Remove the attachments section
    text = text.replace attachmentsRegex, ''
    # Remove the JIRA section
    text = text.replace jiraRegex, ''

    #@logger.info text
    return text

  ###*
  # @param {string} text Markdown content of file
  # @param {string} fullOutFileName Absolute path to resulting file
  # @param {string} breadcrumbs Breadcrumbs to add to the file
  # @return {string} Absolute path to created MD file
  ###
  writeMarkdownFile: (text, fullOutFileName, breadcrumbs) ->
    fullOutDirName = @utils.getDirname fullOutFileName
    @_mkdirp.sync fullOutDirName, (error) ->
      if error
        @logger.error 'Unable to create directory #{fullOutDirName}'

    tempInputFile = fullOutFileName + '~'
    
    # Write the original text without modifying breadcrumbs
    @_fs.writeFileSync tempInputFile, text, flag: 'w'

    command = 'pandoc -f html ' +
      @pandocOptions +
      ' -o "' + fullOutFileName + '"' +
      ' "' + tempInputFile + '"'
    out = @_exec command, cwd: fullOutDirName
    @logger.error out.stderr if out.status > 0

    # Transform breadcrumbs from HTML to "link1>link2>link3"
    if breadcrumbs and  !fullOutFileName.endsWith 'index.md'
      breadcrumbLinks = breadcrumbs.html().match(/<a [^>]+>([^<]+)<\/a>/g)
      #find the title and attachment so its like [title](attachment)
      #<a href="index.html">Web Design Services</a>' turns into (Web Design Services)[index.html]
      for i in [0...breadcrumbLinks.length]
        link = breadcrumbLinks[i]
        title = link.match(/>([^<]+)</)[1]
        href = link.match(/href="([^"]+)"/)[1]
        breadcrumbLinks[i] = "[#{title}](#{href})"
      # @logger.info breadcrumbLinks
      formattedBreadcrumbs = breadcrumbLinks.join(' > ')

      # Now, read the converted Markdown file and add breadcrumbs at the beginning
      finalMarkdown = @_fs.readFileSync(fullOutFileName, 'utf8')
      finalMarkdown = "#{formattedBreadcrumbs}\n\n#{finalMarkdown}"
      
      # Write the final file with breadcrumbs added
      @_fs.writeFileSync(fullOutFileName, finalMarkdown, flag: 'w')
    
    # Remove the temporary file
    @_fs.unlinkSync tempInputFile

  ###*
  # @param {array} indexHtmlFiles Relative paths of index.html files from all parsed Confluence spaces
  # @param {string} dirOut Absolute path to a directory where to place converted MD files
  ###
  writeGlobalIndexFile: (indexHtmlFiles, dirOut) ->
    globalIndex = @_path.join dirOut, 'index.md'
    $content = @formatter.createListFromArray indexHtmlFiles
    text = @formatter.getHtml $content
    @writeMarkdownFile text, globalIndex

module.exports = App