# Copyright 2016 Konrad Edwards
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''Anvil module containing reusable code
   Contents:
   Classes: 
   graph - for creating graph objects that plot a given dataset on their own canvas
   Functions: 
   draw_line - draws a simple line from an origin along a vector
   draw_arrow - draws a simple arrow from an origin along a vector
   draw_spring - draws a malleable spring between two given points, takes a canvas as argument
   sig_round - rounds a given float number (first arg) to a given number of significant figures (second arg)
   int_round - rounds the given float number to the nearest integer, returning an int
   '''

from anvil import *
import math, physics, draw
from physics import vector3
from draw import reset2
import random # Used for default colours

class graph:
   '''Anvil Canvas graph object
      
      Create a graph, on which a dataset is plotted.
      Created in its own canvas, which must be specified as an initialisation argument
      Styles can be modified using parameters.
      For more information on any method, see the method Docstring
      
      Attributes:
      canvas - the canvas on which the graph object exists
      cw, ch - the width and height of the canvas in pixels
      gap - the distance, in pixels, between the ends of the axes and the canvas edge
      data - a dictionary of lists of vector3 objects describing the data points on the graph. Note that the z value is irrelevant to the graph class
      x_range - a two value tuple of the values at the ends of the x axis, (min, max) of the x values of data by default
      y_range - a two value tuple of the values at the ends of the y axis, (min, max) of the y values of data by default
      x_set, y_set - a two value tuple of either("number", number of divisions) or ("width", division width) for system memory
      The scaling factors are multiplied by any value to give a pixelwise position
      scale_x - a scaling factor giving the number of pixels per unit x
      scale_y - a scaling factor giving the number of pixels per unit y
      line_colour - a dictionary of the colour of the line or points plotted on the graph, a string of form "#rrggbb"
      line_wt - a dictionary of the width of the line or points plotted on the graph
      axis_colour - the colour of the axis arrows, a string of the form "#rrggbb"
      axis_wt - the width of the axis arrows, the gridlines, if present, are half this width
      plot_type - a dictionary of strings, takes values of "line" or "points" only, defines the plotting type
      x_gridlines, y_gridlines - booleans turning gridlines on/off, off by default
      x_marks, y_marks - booleans turning on/off text labels along the axes, on by default
      origin - the location, in a bottom left based, upward, pixel coordinate system of the origin of the graph, as a vector3 object
      x_label, y_label - strings, the labels at the ends of the graph axes
      x_divis, y_divis - lists defining the points where gridlines and axis value labels would go if present
      x_sig_figs, y_sig_figs - must be set directly, define the number of significant figures displayed on each axis, default 2
      
      Methods:
      Dictionary setters, set_data, set_data_from_vectors, set_line_colour, set_line_weight, set_plot_type
      all have an optional string argument specifying the dataset by name, which if left default will apply to "graph_1" dataset
      __init__ - Initialises the graph, calls most getters and setters with default values. Does Not Draw The Graph.
      draw - draws the graph in its current state
      clear - called by draw, clears the canvas visually and of any transformations, sets bottom left origin, +ve upward coordinates
      set_data - takes two lists of x values and y values, must be the same length
      set_data_from_vectors - takes a list of vector3 objects to set the data points
      get_data - returns the current dataset of the graph as a list of vector3 objects
      set_x_range, get_x_range - getter and setter, if set is called empty, it sets the default value
      set_y_range, get_y_range - getter and setter, if set is called empty, it sets the default value
      set_y_divisions, get_y_divisions - getter and setter, if set is called empty, it sets the default values of of 10 divisions
      set_x_divisions, get_x_divisions - getter and setter, if set is called empty, it sets the default values of of 10 divisions
      set_plot_type, get_plot_type - getter and setter, setter requires argument of "line" or "points"
      set_line_weight, get_line_weight - getter and setter, if set is called empty, it sets the default value of 1
      set_line_colour, get_line_colour - getter and setter, if set is called empty, it sets the default value
      set_axis_weight, get_axis_weight - getter and setter, if set is called empty, it sets the default value of 1
      set_axis_colour, get_axis_colour - getter and setter, if set is called empty, it sets the default value of dark grey
      set_x_gridlines, set_y_gridlines - setters, take boolean arguments, default to False
      set_x_marks, set_y_marks - setters, take boolean arguments, default to True
      set_x_label, set_y_label - setters, take string arguments
      set_origin, get_origin - setter and getter,  determines the origin automatically, set_origin also sets the scaling factors
      '''
   def __init__(self, canvas, xvals = [], yvals = [], name = "graph_1", x_range = "default", y_range = "default"):
      '''Initialises the graph.
         Does not draw the graph.
         Most variables are initialised using empty calls to their setters.
         '''
      self.canvas = canvas
      self.cw = canvas.get_width()
      self.ch = canvas.get_height()
      self.gap = 40 # Define the gap between the axis ends and the canvas edge
      random.seed(6754) # Constant seed to generate the same random set of colours every time
      # Define the significant figures displayed on the axes
      self.x_sig_figs = 2
      self.y_sig_figs = 2
      #Initialise all dictionaries
      self.line_colour = {}
      self.line_wt = {}
      self.data = {}
      self.plot_type = {}
      # Set attributes to given parameters
      # The scale factors are the number of pixels per unit x or y given
      # These will be set to the needed values when setting the axis ranges
      self.scale_x = 1
      self.scale_y = 1
      # Initialising, these values will always be overwritten
      self.x_range = (-1, 1)
      self.y_range = (-1, 1)
      # This records whether the scale markings and gridline positions are currently
      # set by division number or division width and allows the system to remember how to determine the
      # divisions if an axis range is changed
      self.x_set = ("width", 1)
      self.y_set = ("width", 1)
      # Record given data
      self.datasets = 2 # Record how many datasets there are + 2 (for default colour reasons)
      self.set_data(xvals, yvals, name)
      # Define the division lists
      self.x_divis = []
      self.y_divis = []
      # Set axis ranges, and internally the division lists
      self.set_x_range(x_range)
      self.set_y_range(y_range)
      # Set default line style and init the dicitionaries thereof
      self.set_line_colour("new", name) # "new" tells it to set the colour to the next in the default set
      self.set_line_weight(1, name)
      # Set default axis style
      self.axis_colour = "#222222"
      self.axis_wt = 1
      # Set default plot type
      self.set_plot_type("line", name)
      # default no gridlines
      self.x_gridlines = False
      self.y_gridlines = False
      # Set default graph design
      self.set_origin()
      self.set_x_label()
      self.set_y_label()
      self.set_x_marks()
      self.set_y_marks()
   
   def set_data(self, xvals, yvals, name = "graph_1"):
      '''Sets the internal data set of the graph from two lists of x values and y values.
         Will raise errors if the two are not both lists of the same length.
         '''
      # Check for input errors
      try:
         if len(xvals) is not len(yvals):
            raise ValueError("The x and y datasets must be the same length")
      except TypeError:
         raise TypeError("The x and y datasets must be lists. If you only want one point, use [point]")
      # Change the given two lists into a single vector3 list
      data = list(range(0, len(xvals))) # Make data a list of equivalent length
      for i in list(range(0, len(xvals))):
         data[i] = vector3(xvals[i], yvals[i])
      if name not in self.data: # If this is a new dataset
         self.datasets += 1
         self.set_line_colour("new", name) # Set the plot parameters
         self.set_plot_type("line", name)
         self.set_line_weight(1, name)
      self.data[name] = sorted(data, key=lambda a: a.x)

   def set_data_from_vectors(self, vectset, name = "graph_1"):
      '''Sets the internal data set of the graph from a list of vector3 objects.
         Will raise errors if the argument is not a list, or the components are not vector3 objects.
         '''
      try:
         length = len(vectset) # Check whether the input is a list
         for i in range(length):
            if type(vectset[i]) is not vector3: # Check that all components are vector3 objects
               raise TypeError("All elements of the data input to set_data_from_vectors must be vector3 objects")
         self.data = vectset
      except TypeError:
            raise TypeError("The dataset must be a list. If you only want one point, use [point]")
      if name not in self.data: # If this is a new dataset
         self.datasets += 1
         self.set_line_colour("new", name) # Set the plot parameters
         self.set_line_weight(1, name)
         self.set_plot_type("line", name)
      self.data[name] = sorted(self.data, key=lambda a: a.x)

   def get_data(self, name):
      '''Getter for the internal datasets of the graph.
         Returns the data as a list of vector3 objects.
         '''
      return self.data[name]

   def remove_data(self, name):
      '''Removes the dataset "name" from all relevant internal dictionaries.
         Graph will need to be redrawn to remove the image.
         '''
      if name not in self.data: # Check whether there is a data set "name"
         return # If not, do nothing, as it's already 'removed' if it isn't there
      # Remove all dictionary entries
      del self.data[name]
      del self.line_colour[name]
      del self.line_wt[name]
      del self.plot_type[name]
      # Note that this does not change the dataset number as that only affects the default line colours

   def set_x_range(self, x_range = "default"):
      '''Setter for the value range of the x axis.
         If called empty defaults to setting the minimum and maximum x values in the dataset.
         If called empty with no data in the graph, it will set the axis to run from -10 to 10.
         Will always set to the form (Min, Max)
         '''
      if x_range == "default" and [a for a in [self.data[name] for name in self.data] if a != []] == []:
         x_range = (-10, 10) # Catch the case where no data was specified in any dataset
      elif x_range == "default": # If no input, take the values from the data
         # Finds the extremal values of each dataset, and then the extremals of the extremals
         self.x_range = (min([min(c) for c in[[a.x for a in b] for b in [self.data[name] for name in self.data]]]),
                         max([max(c) for c in[[a.x for a in b] for b in [self.data[name] for name in self.data]]]))
      elif type(x_range) is not tuple or len(x_range) is not 2: # Check the form of the input
         raise ValueError("x_range and y_range must both be two value tuples")
      else:
         self.x_range = x_range
      # Ensure the input is the correct way round and not 0 to 0
      if self.x_range[0] == 0 and self.x_range[1] == 0:
         self.x_range = (-10, 10)
      if self.x_range[0] > self.x_range[1]:
         self.x_range = (self.x_range[1], self.x_range[0])
      # Now set the divisions. Calling this also modifies the range values for justification
      # Checks to see which type of division determination is in use
      if self.x_set[0] == "width":
         self.set_x_division_width(self.x_set[1])
      elif self.x_set[0] == "number":
         self.set_x_division_no(self.x_set[1])
      self.set_origin() # Redetermine the origin and scaling factors
      
   def get_x_range(self):
      '''Getter for the value range of the x axis.
         Returns a two value tuple of (Minimum Value, Maximum Value).
         '''
      return self.x_range

   def set_y_range(self, y_range = "default"):
      '''Setter for the value range of the y axis.
         If called empty defaults to setting the minimum and maximum x values in the dataset.
         If called empty with no data in the graph, it will set the axis to run from -10 to 10.
         Will always set to the form (Min, Max)
         '''
      if y_range == "default" and [a for a in [self.data[name] for name in self.data] if a != []] == []:
         y_range = (-10, 10) # Catch the case where no data was specified
      elif y_range == "default": # If no input, take the values from the data
         # Finds the extremal values of each dataset, and then the extremals of the extremals
         self.y_range = (min([min(c) for c in[[a.y for a in b] for b in [self.data[name] for name in self.data]]]),
                         max([max(c) for c in[[a.y for a in b] for b in [self.data[name] for name in self.data]]]))
      elif type(y_range) is not tuple or len(y_range) is not 2: # Check that the input is of the correct form
         raise ValueError("x_range and y_range must both be two value tuples")
      else:
         self.y_range = y_range
      # Ensure the input is the correct way round
      if self.y_range[0] == 0 and self.y_range[1] == 0:
         self.y_range = (-10, 10)
      if self.y_range[0] > self.y_range[1]:
         self.y_range = (self.y_range[1], self.y_range[0])
      # Now set the divisions. Calling this also modifies the range values for justification
      # Checks to see which type of division determination is in use
      if self.y_set[0] == "width":
         self.set_y_division_width(self.y_set[1])
      elif self.y_set[0] == "number":
         self.set_y_division_no(self.y_set[1])
      self.set_origin() # Redetermine the origin and scaling factors

   def get_y_range(self):
      '''Getter for the value range of the y axis.
         Returns a two value tuple of (Minimum Value, Maximum Value).
         '''
      return self.y_range
   
   def set_x_division_width(self, width = 1.0):
      '''This Method takes a width argument and uses it to set the values in the list of x axis divisions.
         IMPORTANT: This method changes the value of x_range in order to justify the graph about 0 and ensure correct plotting.
         The maximum and minimum values of the x axis will be set to the smallest multiples of the division width
         that allow the original extremal values to be included in the new range.
         '''
      if width <= 0: # Check for an input error
         raise ValueError("The division width must be set to a positive, non-zero number.")
      self.x_set = ("width", width) # Record that the divisions are now determined by division width
      # If-else block ensures that the origin is included in the plot
      if self.x_range[0] >= 0:
         limits = (0, self.x_range[1]) # Start from 0
      elif self.x_range[1] <= 0:
         limits = (self.x_range[0], 0) # End at 0
      else:
         limits = self.x_range # Includes 0 already
      # Set the upper and lower limits to the next multiple of <width> along from their current value
      # Modulo has the sign of the divisor and is rounded toward -ve infinity
      limits = (limits[0] - limits[0]%width, limits[1] + (-1 * limits[1])%width)
      self.x_divis = [] # Generate and/or clear the list of divisions
      for i in list(range(1 + int_round((limits[1] - limits[0])/width))): # Need one more value than the division number
         # Since both limits are multiples of width, add a number of widths to get each division edge
         self.x_divis += [limits[0] + width * i]
      self.x_range = limits # Now set the object variable to the new limits to ensure correct scaling is achieved
      self.set_origin() # Redetermine the origin and scaling factors
         
      
   def set_x_division_no(self, num = 10):
      '''This Method takes an argument of the desired number of divisions along the axis, and sets the values
         in the list of x axis divisions.
         IMPORTANT: This method changes the value of x_range in order to justify the graph about 0 and ensure correct plotting.
         The maximum or minimum value of the x axis will be set such that there are an integer number of divisions either
         side of the origin, and that the original extremal values are included in the new range.
         '''
      if num <= 0 or type(num) is not int: # Check for an input error
         raise ValueError("The number of divisions must be set to a positive, non-zero integer.")
      self.x_set = ("number", num) # Record that the divisions are now determined by division width
      # If-else block ensures the origin is included in the plot
      if self.x_range[0] >= 0:
         limits = (0, self.x_range[1]) # Start from 0
         step = (limits[1] - limits[0]) / num # range length is now the upper limit, which is +ve
         self.x_divis = [] # Generate and/or clear the list of divisions
         for i in list(range(num + 1)): # Generate list by stepping from 0 to upper limit
            self.x_divis += [limits[0] + i * step] # in steps of upper limit / number of steps
      elif self.x_range[1] <= 0:
         limits = (self.x_range[0], 0) # End at 0
         step = (limits[1] - limits[0]) / num # range length is now |lower limit|, lower limit is -ve
         self.x_divis = [] # Generate and/or clear the list of divisions
         for i in list(range(num + 1)): # Generate list by stepping from lower limit to 0
            self.x_divis += [limits[0] + i * step] # in steps of |lower limit| / number of steps
      else:
         limits = self.x_range # Includes 0 already
         step = (limits[1] - limits[0]) / num # Find initial step length to give correct number of divisions
         self.x_divis = [] # Generate and/or clear the list of divisions
         for i in list(range(num + 1)): # Generate initial list by stepping from lower to upper limit
            self.x_divis += [limits[0] + i * step] # in steps of total range / number of steps
         # Sort according to distance from 0
         order = sorted(self.x_divis, key=lambda a: abs(a))
         # Principle of the following is that it widens the divisions to push the closest value to 0 to 0.
         # The side that didn't include the closest value will thus extend now past the original extent
         if order[0] < 0: # If the closest value to 0 is -ve
            self.x_range = limits # Tell the width function what the current extents are
            # The new width will be (the length from min to 0) / (the number of divisions between min and the one being pushed to 0)
            self.set_x_division_width(abs(limits[0])/self.x_divis.index(order[0]))
            self.x_set = ("number", num) # Width() records this as width, so change it back
         if order[0] > 0: # If the closest value to 0 is +ve
            self.x_range = limits # Tell the width function what the current extents are
            # The new width will be (the length from 0 to max) / (the number of divisions between the one being pushed to 0 and max)
            self.set_x_division_width(limits[1]/(len(self.x_divis) - self.x_divis.index(order[0])))
            self.x_set = ("number", num) # Width() records this as width, so change it back
         self.x_range = limits # Now set the object variable to the new limits to ensure correct scaling is achieved
         self.set_origin() # Redetermine the origin and scaling factors
         
   def set_y_division_width(self, width = 1.0):
      '''This Method takes a width argument and uses it to set the values in the list of y axis divisions.
         IMPORTANT: This method changes the value of y_range in order to justify the graph about 0 and ensure correct plotting.
         The maximum and minimum values of the y axis will be set to the smallest multiples of the division width
         that allow the original extremal values to be included in the new range.
         '''
      if width <= 0: # Check for an input error
         raise ValueError("The division width must be set to a positive, non-zero number.")
      self.y_set = ("width", width) # Record that the divisions are now determined by division width
      # If-else block ensures that the origin is included in the plot
      if self.y_range[0] >= 0:
         limits = (0, self.y_range[1]) # Start from 0
      elif self.y_range[1] <= 0:
         limits = (self.y_range[0], 0) # End at 0
      else:
         limits = self.y_range # Includes 0 already
      # Set the upper and lower limits to the next multiple of <width> along from their current value
      # Modulo has the sign of the divisor and is rounded toward -ve infinity
      limits = (limits[0] - limits[0]%width, limits[1] + (-1 * limits[1])%width)
      self.y_divis = [] # Generate and/or clear the list of divisions
      for i in list(range(1 + int_round((limits[1] - limits[0])/width))): # Need one more value than the division number
         # Since both limits are multiples of width, add a number of widths to get each division edge
         self.y_divis += [limits[0] + width * i]
      self.y_range = limits # Now set the object variable to the new limits to ensure correct scaling is achieved
      self.set_origin() # Redetermine the origin and scaling factors
      
   def set_y_division_no(self, num = 10):
      '''This Method takes an argument of the desired number of divisions along the axis, and sets the values
         in the list of y axis divisions.
         IMPORTANT: This method changes the value of y_range in order to justify the graph about 0 and ensure correct plotting.
         The maximum or minimum value of the y axis will be set such that there are an integer number of divisions either
         side of the origin, and that the original extremal values are included in the new range.
         '''
      if num <= 0 or type(num) is not int: # Check for an input error
         raise ValueError("The number of divisions must be set to a positive, non-zero integer.")
      self.y_set = ("number", num) # Record that the divisions are now determined by division width
      # If-else block ensures the origin is included in the plot
      if self.y_range[0] >= 0:
         limits = (0, self.y_range[1]) # Start from 0
         step = (limits[1] - limits[0]) / num # range length is now the upper limit, which is +ve
         self.y_divis = [] # Generate and/or clear the list of divisions
         for i in list(range(num + 1)): # Generate list by stepping from 0 to upper limit
            self.y_divis += [limits[0] + i * step] # in steps of upper limit / number of steps
      elif self.y_range[1] <= 0:
         limits = (self.y_range[0], 0) # End at 0
         step = (limits[1] - limits[0]) / num # range length is now |lower limit|, lower limit is -ve
         self.y_divis = [] # Generate and/or clear the list of divisions
         for i in list(range(num + 1)): # Generate list by stepping from lower limit to 0
            self.y_divis += [limits[0] + i * step] # in steps of |lower limit| / number of steps
      else:
         limits = self.y_range # Includes 0 already
         step = (limits[1] - limits[0]) / num # Find initial step length to give correct number of divisions
         self.y_divis = [] # Generate and/or clear the list of divisions
         for i in list(range(num + 1)): # Generate initial list by stepping from lower to upper limit
            self.y_divis += [limits[0] + i * step] # in steps of total range / number of steps
         # Sort according to distance from 0
         order = sorted(self.y_divis, key=lambda a: abs(a))
         # Principle of the following is that it widens the divisions to push the closest value to 0 to 0.
         # The side that didn't include the closest value will thus extend now past the original extent
         if order[0] < 0: # If the closest value to 0 is -ve
            self.y_range = limits # Tell the width function what the current extents are
            # The new width will be (the length from min to 0) / (the number of divisions between min and the one being pushed to 0)
            self.set_y_division_width(abs(limits[0])/self.y_divis.index(order[0]))
            self.y_set = ("number", num) # Width() records this as width, so change it back
         if order[0] > 0: # If the closest value to 0 is +ve
            self.y_range = limits # Tell the width function what the current extents are
            # The new width will be (the length from 0 to max) / (the number of divisions between the one being pushed to 0 and max)
            self.set_y_division_width(limits[1]/(len(self.y_divis) - self.y_divis.index(order[0])))
            self.y_set = ("number", num) # Width() records this as width, so change it back
         self.y_range = limits # Now set the object variable to the new limits to ensure correct scaling is achieved
         # Now set the scaling factor, as defined above, the 0.0s are to avoid integer division
         if self.y_range[0] >= 0: # If the axis is 0 -> y max
            self.scale_y = (self.ch - (2 * self.gap) + 0.0) / self.y_range[1]
         elif self.y_range[1] <= 0: # If the axis is y min -> 0
            self.scale_y = (self.ch - (2 * self.gap) + 0.0) / abs(self.y_range[0])
         else: # If the axis is y min -> y max
            self.scale_y = (self.ch - (2 * self.gap) + 0.0) / (self.y_range[1] - self.y_range[0])
         self.set_origin() # Redermine the origin and scaling factors
   
   def get_x_divisions(self):
      '''Getter for the divisions of the x axis.
         Returns a list of the values which will be labeled if x marks are switched on.
         '''
      return self.x_divis

   def get_y_divisions(self):
      '''Getter for the divisions of the y axis.
         Returns a list of the values which will be labeled if y marks are switched on.
         '''
      return self.y_divis

   def set_plot_type(self, typestr, name = "graph_1"):
      '''Setter for the Plot Type of the graph.
         Takes a string argument, will raise an error if the argument is not "line" or "points".
         Line draws lines between consecutive points. 
         Points draws a circle with diameter equal to the line width at each data point.
         '''
      if typestr is not "line" and typestr is not "points": # Checks that the input is correct and raises an error if not
         raise ValueError("plot type must be a string, and be either 'line' or 'points'")
      else:
         self.plot_type[name] = typestr

   def get_plot_type(self, name = "graph_1"):
      '''Getter for the Plot Type.
         Returns a string with the plot type, "line" or "points".
         '''
      return self.plot_type[name]

   def set_line_weight(self, wt, name = "graph_1"):
      '''Setter for the line weight. 
         Argument gives the width in pixels of the graph line, or 1/3 the diameter in pixels of graph points
         '''
      self.line_wt[name] = wt

   def get_line_weight(self, name = "graph_1"):
      '''Getter for the Line Weight.
         Returns a number.
         '''
      return self.line_wt[name]
   
   def set_line_colour(self, colstr, name = "graph_1"):
      '''Setter for the line colour, the colour of any line or points plotted.
         Argument must be a string of form "#rrggbb" in hexadecimals
         '''
      if colstr == "new":
         # Determines the default for a new line randomly, but will be the same every graph (constant seed)
         cols = [0,1,2]
         for i in cols:
            cols[i] = (random.randint(0,255) + 200)/2
         colstr = "#{0:x}{1:x}{2:x}".format(cols[0], cols[1], cols[2])
      # Check that the colour string is of the correct form
      if type(colstr) is not str or ( len(colstr) is not 7 and len(colstr) is not 4 ) :
         raise ValueError("Argument must be a string of form '#rrggbb' in hexadecimals")
      
      self.line_colour[name] = colstr
   
   def get_line_colour(self, name = "graph_1"):
      '''Getter for the Line Weight.
         Returns a string of the form "#rrggbb" in hexadecimals.
         '''
      return self.line_colour[name]
   
   def set_axis_weight(self, wt):
      '''Setter for the axis weight.
         Argument gives the width in pixels of the axis arrows. Gridlines, if present, are half this width.
         '''
      self.axis_wt = wt
   
   def get_axis_weight(self):
      '''Getter for the Axis Weight.
         Returns a number.
         '''
      return self.axis_wt
   
   def set_axis_colour(self, colstr):
      '''Setter for the axis colour, the colour of the axis arrows and, if present, gridlines.
         Argument must be a string of form "#rrggbb" in hexadecimals
         '''
      # Check that the colour string is of the correct form
      if type(colstr) is not str or ( len(colstr) is not 7 and len(colstr) is not 4 ) :
         raise ValueError("Argument must be a string of form '#rrggbb' in hexadecimals")
      self.axis_colour = colstr
   
   def get_axis_colour(self):
      '''Getter for the Line Weight.
         Returns a string of the form "#rrggbb" in hexadecimals.
         '''
      return self.axis_colour
   
   def set_x_gridlines(self, yn):
      '''Turns x gridlines on/off.
         Note that x gridlines are those along the x axis and are thus lines in the y direction.
         '''
      if type(yn) == bool: # Check the input is of the correct form
         self.x_gridlines = yn
      else:
         raise TypeError("Must set gridlines as True or False (on/off)")

   def set_y_gridlines(self, yn):
      ''' Turns y gridlines on/off.
         Note that y gridlines are those along the y axis and are thus lines in the x direction.
         '''
      if type(yn) == bool: # Check the input is of the correct form
         self.y_gridlines = yn
      else:
         raise TypeError("Must set gridlines as True or False (on/off)")

   def set_x_label(self, lab = "x"):
      '''Setter for the x axis label.
         Takes a string argument which is printed at the end of the x axis.
         If called empty, sets the label to "x".
         '''
      self.x_label = lab

   def set_y_label(self, lab = "y"):
      '''Setter for the y axis label.
         Takes a string argument which is printed at the end of the y axis.
         If called empty, sets the label to "y".
         '''
      self.y_label = lab
   
   def set_x_marks(self, yn = True):
      '''On/Off switch for x marks.
         If True, will print the values of x divisions at the relevant points along the x axis.
         If False, the axis will be clear, with no number along them.
         '''
      if type(yn) == bool: # Check the input is of the correct form
         self.x_marks = yn
      else:
         raise TypeError("Must set X marks as True or False (on/off)")
   
   def set_y_marks(self, yn = True):
      '''On/Off switch for y marks.
         If True, will print the values of y divisions at the relevant points along the y axis.
         If False, the axis will be clear, with no number along them.
         '''
      if type(yn == bool): # Check the input is of the correct form
         self.y_marks = yn
      else:
         raise TypeError("Must set Y marks as True or False (on/off)")
   
   def set_origin(self, origin = "default"):
      '''Sets the origin and the scaling factors for drawing the graph.
         The origin is a vector object which is used in drawing the graph to determine where the crossing 
         point of the axes, (0, 0) is on the canvas.
         The scaling factors are floats giving the number of pixels per unit on the x, y axes.
         '''
      if type(origin) is not vector3 and origin is not "default": # Need a vector
         raise TypeError("the origin must be set to a vector coordinate")
      elif origin == "default": # Check whether we are in default origin mode
         # Now set the scaling factors, as defined above, the 0.0s are to avoid integer division
         if self.x_range[0] >= 0: # If the axis is 0 -> x max
            self.scale_x = (self.cw - 2 * self.gap + 0.0) / self.x_range[1]
         elif self.x_range[1] <= 0: # If the axis is x min -> 0
            self.scale_x = (self.cw - 2 * self.gap + 0.0) / abs(self.x_range[0])
         else: # If the axis is x min -> x max
            self.scale_x = (self.cw - 2 * self.gap + 0.0) / (self.x_range[1] - self.x_range[0])
         if self.y_range[0] >= 0: # If the axis is 0 -> y max
            self.scale_y = (self.ch - (2 * self.gap) + 0.0) / self.y_range[1]
         elif self.y_range[1] <= 0: # If the axis is y min -> 0
            self.scale_y = (self.ch - (2 * self.gap) + 0.0) / abs(self.y_range[0])
         else: # If the axis is y min -> y max
            self.scale_y = (self.ch - (2 * self.gap) + 0.0) / (self.y_range[1] - self.y_range[0])
         # Note the self.gaps here are the gap between the axis ends and the canvas edge
         if self.x_range[0] >= 0 and self.y_range[0] >= 0:
            self.origin = vector3(self.gap, self.gap) # Bottom left corner if only top right quadrant needed
         elif self.x_range[0] >= 0 and self.y_range[1] <= 0:
            self.origin = vector3(self.gap, self.ch - self.gap) # Top left corner if only bottom right quadrant needed
         elif self.x_range[1] <= 0 and self.y_range[0] >= 0:
            self.origin = vector3(self.cw - self.gap, self.gap) # Bottom right corner if only top left quadrant needed
         elif self.x_range[1] <= 0 and self.y_range[1] <= 0:
            self.origin = vector3(self.cw - self.gap, self.ch - self.gap) # Top right corner if only bottom left quadrant needed
         elif self.x_range[0] >= 0: # If only the right half is needed
            self.origin = vector3(self.gap, -1 * self.y_range[0] * self.scale_y + self.gap)
         elif self.x_range[1] <= 0: # If only the left half is needed
            self.origin = vector3(self.cw - self.gap, -1 * self.y_range[0] * self.scale_y + self.gap)
         elif self.y_range[0] >= 0: # If only the top half is needed
            self.origin = vector3(-1 * self.x_range[0] * self.scale_x + self.gap, self.gap)
         elif self.y_range[1] <= 0: # If only the bottom half is needed
            self.origin = vector3(-1 * self.x_range[0] * self.scale_x + self.gap, self.cw - self.gap)
         else: # Otherwise all four quadrants are needed
            self.origin = vector3(-1 * self.x_range[0] * self.scale_x + self.gap, -1 * self.y_range[0] * self.scale_y + self.gap)
      else:
         self.origin = origin # If they have specified an origin

   def get_origin(self):
      '''Getter for origin.
         Returns the location on the canvas of the crossing point of the axes, as a vector3 object.
         '''
      return self.origin

   def draw(self):
      '''Calling this method draws the graph, overwriting anything currently on the graph's canvas.
         '''
      # Clear the canvas and set vertical to upward
      self.clear()
      
      self.set_origin() # Make sure the origin position and scaling factors are up to date
      
      # Draw the axes - the self.gaps and (2 * self.gap)s just leave a gap between axis ends and the canvas edge
      # This is simpler without translation to the origin, so that isn't done yet
      # The axis objects are just vectors of the correct length and direction
      xaxis = vector3(self.cw - (2 * self.gap), 0)
      yaxis = vector3(0, self.ch - (2 * self.gap))
      draw_line(self.canvas, vector3(self.gap, self.origin.y), xaxis, self.axis_wt, self.axis_colour)
      draw_line(self.canvas, vector3(self.origin.x, self.gap), yaxis, self.axis_wt, self.axis_colour)
      # Now add arrows at the ends of the axis
      draw_arrow(self.canvas, vector3(self.gap, self.origin.y) + xaxis, vector3(10, 0), self.axis_wt, self.axis_colour)
      draw_arrow(self.canvas, vector3(self.origin.x, self.gap) + yaxis, vector3(0, 10), self.axis_wt, self.axis_colour)
      # If wanted, draw the gridlines
      if self.x_gridlines is True:
         for x in self.x_divis:
            draw_line(self.canvas, vector3(self.origin.x + self.scale_x * x, self.gap), yaxis, 0.5 * self.axis_wt, self.axis_colour)
      if self.y_gridlines is True:
         for y in self.y_divis:
            draw_line(self.canvas, vector3(self.gap, self.origin.y + self.scale_y * y), xaxis, 0.5 * self.axis_wt, self.axis_colour)

      # Add the text to the graph
      # For the text sections all plotting y values are multiplied by -1 to compensate for the coord flip
      # Text is in general drawn half the gap distance from the relevant axis point
      self.canvas.fill_style = "#000"
      # Start with the labels, these are the last objects not to use the new origin to draw from
      self.canvas.font = "12px sans-serif"
      self.canvas.scale(1, -1) # Need to temporarily flip the coordinates or the text ends up upside down
      self.canvas.text_align = "left"
      self.canvas.text_baseline = "bottom"
      self.canvas.fill_text(self.x_label, 0.5 * self.cw - 0.5 * self.canvas.measure_text(self.x_label), -1 * self.axis_wt) # Baseline just above the edge of the canvas
      self.canvas.text_align = "left"
      self.canvas.text_baseline = "top"
      self.canvas.reset_transform() # For ease of use
      self.canvas.translate(self.axis_wt, 0.5 * self.ch + 0.5 * self.canvas.measure_text(self.y_label)) # "Top" of the rotated text just offset from the edge of the canvas
      self.canvas.rotate(math.pi / -2) # Rotate y-axis label
      self.canvas.fill_text(self.y_label, 0, 0)
      reset2(self.canvas, 1) # Reset to vertical positive, bottom left origin
      
      # Set the origin for all future drawing operations (until clear() is called)
      self.canvas.translate(self.origin.x, self.origin.y)
      
      # If gridlines are not on, draw tick marks for positions along the axis
      # Tick marks are 3 pixels long
      if self.x_gridlines is False:
         for x in self.x_divis:
            draw_line(self.canvas, vector3(x * self.scale_x, 0), vector3(0, -3))
      if self.y_gridlines is False:
         for y in self.y_divis:
            draw_line(self.canvas, vector3(0, y * self.scale_y), vector3(-3, 0))

      # Continue adding text with the new origin
      self.canvas.font = "10px sans-serif"
      self.canvas.scale(1, -1) # Need to temporarily flip the coordinates or the text ends up upside down
      if self.x_marks is True:
         self.canvas.text_align = "right"
         self.canvas.text_baseline = "top"
         for x in self.x_divis:
            self.canvas.fill_text("{0}".format(sig_round(x, self.x_sig_figs)), x * self.scale_x - self.axis_wt, self.axis_wt)
      if self.y_marks is True:
         self.canvas.text_align = "right"
         self.canvas.text_baseline = "top"
         # This now removes the closest element in y to 0, to avoid labelling 0 on both axes
         # and to account for floats possibly not being exactly 0
         for y in [a for a in self.y_divis if abs(a) != min([abs(b) for b in self.y_divis])]:
            self.canvas.fill_text("{0}".format(sig_round(y, self.y_sig_figs)), -1, -1 * y * self.scale_y)
      self.canvas.scale(1, -1) # Need to temporarily flip the coordinates or the text ends up upside down

      # Now plot the dataset
      for name in self.data:
         if self.plot_type[name] == "line":
            self.canvas.stroke_style = self.line_colour[name]
            self.canvas.line_width = self.line_wt[name]
            prev = self.data[name][0] # Keep note of the previous data point
            self.canvas.begin_path()
            for point in self.data[name]: # Draw a line between the previous data point and current for each point
               self.canvas.move_to(prev.x * self.scale_x, prev.y * self.scale_y)
               self.canvas.line_to(point.x * self.scale_x, point.y * self.scale_y)
               prev = vector3(point.x, point.y) # Note that the current point is now the previous point
            self.canvas.stroke() # Draw the whole line
         elif self.plot_type[name] == "points":
            self.canvas.fill_style = self.line_colour[name]
            r = 1.5 * self.line_wt[name]
            for point in self.data[name]: # Draw a circle of diameter 3x the line width at each data point (for visibility)
               self.canvas.begin_path()
               self.canvas.arc(point.x * self.scale_x, point.y * self.scale_y, r)
               self.canvas.fill()

   def clear(self):
      '''Wipes the canvas and resets transformations.
         The wipe colour is a very light grey.
         The canvas system is set to bottom left origin (not to be confused with graph.origin)
         The canvas system is set to have horizontal left -> right, vertical bottom -> top.
         '''
      reset2(self.canvas, 1) # Vertical upward becomes +ve, origin of canvas set to bottom left
      self.canvas.fill_style = "#f5f5f5"
      self.canvas.fill_rect(0, 0, self.cw, self.ch) # Wipe with light grey

# Start of Functions

def draw_line(canvas, start, vect, width = 1, colour = "#222222"):
   '''Draw a simple line from start along vect'''
   canvas.stroke_style = colour
   canvas.line_width = width
   end = start + vect
   canvas.begin_path()
   canvas.move_to(start.x, start.y)
   canvas.line_to(end.x, end.y) # Draw the line
   canvas.stroke()

def draw_arrow(canvas, start, vect, width = 1, colour = "#222222"):
   '''Draw a simple arrow from start along vect, with a fixed size (10px) arrowhead.'''
   canvas.stroke_style = colour
   canvas.line_width = width
   end = start + vect
   direction = vect.norm() # Arrow direction
   canvas.begin_path()
   canvas.move_to(start.x, start.y) # Draw the main line
   canvas.line_to(end.x, end.y)
   flick = direction.phi_rotate(-5*math.pi/6, vector3(0, 0)) # Direction of one of the arrow tip lines
   flick *= 8 # Length of the arrow end lines
   canvas.line_to(end.x + flick.x, end.y + flick.y) # Draw one line of the arrow tip
   flick = direction.phi_rotate(5*math.pi/6, vector3(0, 0)) # Direction of the other arrow tip line
   flick *= 8
   canvas.move_to(end.x, end.y)
   canvas.line_to(end.x + flick.x, end.y + flick.y) # Draw the other line of the arrow tip
   canvas.stroke()

def draw_spring(canvas, start, end, width, line_width = 1, colour = "#222222"):
   ''' Draw a spring between two points, specified as vector objects using the physics module for anvil.
      canvas must be an anvil canvas in the parent Form.
      start, end must be vector3 objects, although the z-component is not used.
      width specifies the width of the zig-zags of the spring
      line_width and colour give the line style used for the spring
      colour must be a #rrggbb string in hexadecimal
      '''
   section = (end - start)/6 # Length of a section of the spring, a more useful measure of it's length
   direction = (end - start).norm() # Direction of the spring
   sideways = 0.5 * width * direction.phi_rotate(math.pi/2, vector3(0,0)) # Vector giving sideways offset to corners
   pencil = vector3(start.x, start.y) # Vector to keep track of drawing position
   canvas.stroke_style = colour
   canvas.line_width = line_width
   canvas.begin_path()
   canvas.move_to(pencil.x, pencil.y)
   pencil += section
   canvas.line_to(pencil.x, pencil.y) # Draw the first flat section
   pencil += 0.5 * section + sideways
   canvas.line_to(pencil.x, pencil.y) # Draw the first half diagonal
   pencil += section - 2 * sideways
   canvas.line_to(pencil.x, pencil.y) # Draw the next diagonal
   pencil += section + 2 * sideways
   canvas.line_to(pencil.x, pencil.y) # Draw the next diagonal
   pencil += section - 2 * sideways
   canvas.line_to(pencil.x, pencil.y) # Draw the next diagonal
   pencil += 0.5 * section + sideways
   canvas.line_to(pencil.x, pencil.y) # Draw the last half diagonal
   pencil += section
   canvas.line_to(pencil.x, pencil.y) # Draw the last flat section
   canvas.stroke()

def sig_round(num, sigs):
   '''Rounds a float number (First Argument) to the specified number of significant figures (Second Argument).
      Returns a float.
      '''
   if num != 0:
      return round(num, sigs - 1 - int_round(math.floor(math.log10(abs(num)))))
   else:
      return num


def int_round(num):
   '''Rounds an argument to the nearest integer, returning an integer.
      '''
   upper = math.ceil(num)
   lower = math.floor(num)
   if upper - num <= num - lower:
      if upper >= 0:
         return int(upper + 0.1)
      else:
         return int(upper - 0.1)
   else:
      if lower >= 0:
         return int(lower + 0.1)
      else:
         return int(lower - 0.1)



