class Utils

  ###*
  # @param {fs} _fs Required lib
  # @param {path} _path Required lib
  # @param {ncp} _ncp Required lib
  # @param {Logger} logger My lib
  ###
  constructor: (@_fs, @_path, @_ncp, @logger) ->


  mkdirSync: (path) ->
    @logger.debug "Making dir: " + path
    try
      @_fs.mkdirSync path
    catch e
      throw e if e.code isnt 'EEXIST'


  ###*
  # Checks if given file exists and is a file.
  # @param {string} filePath Absolute/relative path to a file
  # @param {string|void} cwd Current working directory against which the path is built.
  # @return {bool}
  ###
  isFile: (filePath, cwd = '') ->
    pathFull = @_path.resolve cwd, filePath
    @_fs.existsSync(pathFull) \
      && ((stat = @_fs.statSync(pathFull)) && stat.isFile())


  ###*
  # Checks if given directory exists and is a directory.
  # @param {string} dirPath Absolute/relative path to a directory
  # @param {string|void} cwd Current working directory against which the path is built.
  # @return {bool}
  ###
  isDir: (dirPath, cwd = '') ->
    pathFull = @_path.resolve cwd, dirPath
    @_fs.existsSync(pathFull) \
      && ((stat = @_fs.statSync(pathFull)) && stat.isDirectory())


  ###*
  # Return list of files (and directories) in a given directory.
  # @param {string} path Absolute path to a directory.
  # @param {bool|void} filesOnly Whether to return only files.
  # @return {array}
  ###
  readDirRecursive: (path, filesOnly = true) ->
    fullPaths = []
    return [path] if @isFile path
    for fileName in @_fs.readdirSync path
      fullPath = @_path.join path, fileName
      if @isFile fullPath
        fullPaths.push fullPath
      else
        fullPaths.push fullPath if not filesOnly
        fullPaths.push @readDirRecursive(fullPath, filesOnly)...
    fullPaths

    
  ###*
  # Sanitize a filename, replacing invalid characters with an underscore
  # @param (string) filename Filename and extension, but not directory component
  # @return (string)
  ###
  sanitizeFilename: (name) ->
    # Restrictions based on Windows. *nix systems only reserve a subset of this list.
    #    (space)
    # <> (less than, greater than)
    # () (parentheses)
    # [] (square brackets)
    # {} (curly braces)
    # :; (colon variants)
    # "'`(quote variants)
    # /  (forward slash)
    # \  (backslash)
    # |  (vertical bar or pipe)
    # ?  (question mark)
    # *  (asterisk)
    #    (other punctuation, while not strictly invalid, can lead to errors if copy-pasting filenames into shells or scripts)
    # Finally, collapse multiple contiguous underscores into a single underscore
    name.replace(/[\s<>()\[\]{}:;'`"\/\\|?\*~!@#$%^&,]/g, '_').replace(/__+/g, '_')


  getBasename: (path, extension) ->
    @_path.basename path, extension


  getDirname: (path) ->
    @_path.dirname path


  readFile: (path) ->
    @_fs.readFileSync path, 'utf8'


  getLinkToNewPageFile: (href, pages, space) ->
    fileName = @getBasename href
    #@logger.debug "href: #{href}"
    #@logger.debug "space: #{space}"
    # relative link to file
    if fileName.endsWith '.html'
      baseName = fileName.replace '.html', '' # gitit requires link to pages without .md extension
      #baseName = baseName.replace '.md', ''
      #@logger.debug "baseName: #{baseName}"
      for page in pages
        #@logger.debug "page.fileBaseName: #{page.fileBaseName}"
        #@logger.debug "page.space: #{page.space}"
        if baseName == page.fileBaseName
          if space == page.space
            #@logger.debug "page.fileNameNew: #{page.fileNameNew}"
            return page.fileNameNew
          else
            return page.spacePath

    # link to confluence pageId
    else if matches = href.match /.*pageId=(\d+).*/
      pageId = matches[1]
      for page in pages
        if pageId == page.fileBaseName
          return page.spacePath.replace '.md', '.md' # gitit requires link to pages without .md extension

    # link outside
    else
      undefined


  ###*
  # Copies assets directories to path with MD files
  # @param {string} fullInPath Absolute path to file to convert
  # @param {string} dirOut Directory where to place converted MD files
  ###
  copyAssets: (pathWithHtmlFiles, dirOut) ->
    for asset in ['images', 'attachments']
      assetsDirIn = @_path.join pathWithHtmlFiles, asset
      assetsDirOut = @_path.join dirOut, asset
      @_ncp assetsDirIn, assetsDirOut if @isDir(assetsDirIn)


module.exports = Utils
