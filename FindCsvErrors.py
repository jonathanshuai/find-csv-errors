import sublime
import sublime_plugin

import csv


class FindCsvErrorsCommand(sublime_plugin.TextCommand):
  delimiter = ','
  text_qualifier = '"'
  read_tag = "[seen]"
  len_read_tag = len(read_tag)

  menu, warning_text, warning_lines = [], [], []
  n_samples = 0

  def run(self, edit):
    # If there are no cached errors
    if self.menu == []:
      # Get the contents of the page (this should be changed later to be optimized for large files)
      contents = self.view.substr(sublime.Region(0, self.view.size()))
      contents = [c + '\n' for c in contents.split('\n')]

      # Get the warning info and lines
      self.n_samples, self.warning_text, self.warning_lines = self.get_warnings(contents)

      # Add information to the menu about number of samples parsed
      self.menu.append("[Copy errors] ({} samples were parsed)".format(self.n_samples))
      self.menu.append("[Clear search]")
      self.menu.extend(self.warning_text)

    # Display a menu for jumping to the error lines
    sublime.active_window().show_quick_panel(self.menu, self.select_option)
  

  def get_warnings(self, contents):
    '''
    Get the lines that should be examined for errors
    '''
    warning_text = []
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
        
        warning_text.append(info_message)
        warning_lines.append((from_line, to_line))

      # Make sure number of fields matches the columns
      n_fields = len(row)

      if n_fields != n_cols:
        info_message = ("[Line {}] Error: Number of fields ({}) don't match columns ({})"
                        .format(parsed.line_num, n_fields, n_cols))
        warning_text.append(info_message)
        warning_lines.append((parsed.line_num, parsed.line_num))

    return n_samples, warning_text, warning_lines

  def select_option(self, menu_index):
    '''
    Handle the selection from the quick panel menu
    '''

    # If no option is selected, do nothing
    if menu_index == -1:
      return
    
    # Option 1: Write to buffer
    if menu_index == 0:
      error_log = sublime.active_window().new_file()
      error_log.set_scratch(True)
      error_log.set_name("error_log.txt")
      
      for (line1, line2) in self.warning_lines:
        region = self.get_region_at_line(line1, line2)
        rows_to_write = self.view.substr(region) + "\n"

        print("{}, {}".format(line1, line2))
        print(rows_to_write)
        
        error_log.run_command("insert", {"characters": rows_to_write})
      
    # Option 2: Clear the search
    elif menu_index == 1:
      self.menu = []

    # Go to line warning_lines[warning_index] 
    else:
      warning_index = menu_index - 2 # Index for warning corresponding to menu index
      self.view.run_command("goto_line", {"line": self.warning_lines[warning_index][0]})

      # Check if the menu item was marked visited yet
      if self.menu[menu_index][-self.len_read_tag:] != self.read_tag:
        self.menu[menu_index] +=  " " + self.read_tag # Mark visited?

  def get_region_at_line(self, line1, line2):
    a = self.view.text_point(line1 - 1, 0)
    b = self.view.text_point(line2 - 1, 0)
    return self.view.line(sublime.Region(a, b))
