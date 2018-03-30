import sublime
import sublime_plugin

import csv


class FindCsvErrorsCommand(sublime_plugin.TextCommand):
  delimiter = ','
  text_qualifier = '"'

  warning_info, warning_lines = [], []

  def run(self, edit):
    # If there are no cached errors
    if self.warning_info == []:
      # Get the contents of the page (this should be changed later to be optimized for large files)
      contents = self.view.substr(sublime.Region(0, self.view.size()))
      contents = [c + '\n' for c in contents.split('\n')]

      # Get the warning info and lines
      self.warning_info, self.warning_lines = self.get_warnings(contents)
      sublime.set_clipboard('\n'.join(self.warning_info))

    # Display a menu for jumping to the error lines
    sublime.active_window().show_quick_panel(self.warning_info, self.select_option)


  def get_warnings(self, contents):
    '''
    Get the lines that should be examined for errors
    '''
    warning_info = []
    warning_lines = []
    
    parsed = csv.reader(contents, delimiter=self.delimiter, 
                        quotechar=self.text_qualifier)

    # Get the header
    n_cols = len(next(parsed))
    n_samples = 0

    # Iterate through the actual data rows
    for row in parsed:
      # Keep track of the sample number
      n_samples += 1

      # Warn for any newlines that were parsed as text
      n_newlines = sum([s.count('\n') for s in row])
      if n_newlines > 0:
        from_line = parsed.line_num - n_newlines
        to_line = parsed.line_num
        info_message = ("[Line {}-{}] Warning: newline was parsed as text on lines"
                        .format(from_line, to_line))
        
        warning_info.append(info_message)
        warning_lines.append(from_line)

      # Make sure number of fields matches the columns
      n_fields = len(row)

      if n_fields != n_cols:
        info_message = ("[Line {}] Error: Number of fields ({}) don't match columns ({})"
                        .format(parsed.line_num, n_fields, n_cols))
        warning_info.append(info_message)
        warning_lines.append(parsed.line_num)

    warning_info.append("[Clear Search] ({} samples were parsed)".format(n_samples))
    return warning_info, warning_lines

  def select_option(self, index):
    '''
    Handle the selection from the quick panel menu
    '''

    # If no option is selected, do nothing
    if index == -1:
      return
    
    # Clear the search if the last option was selected
    if index == len(self.warning_lines):
      self.warning_info = []
      self.warning_lines = []

    # Go to line warning_line[index]
    else:
      self.view.run_command("goto_line", {"line": self.warning_lines[index]})
      self.warning_info[index] +=  " [seen]" # Mark visited?