# Copyright 2016 James Twigg
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

### Version 1.0 - previous versions omit the circuit container class,
### the switch class, the clicked_resistor() method, and some changes
### to how labels and arrows are coloured.

"""Module facilitating the drawing of electrical circuits and components, 
and labelling thereof. Components are placed on a grid of nodes 20px spaced.

Parent Class:
component | parent class collecting code which initialises each component and various
            oft-used graphical commands. Class methods as follow:
            __init__        | instantiates an object based on given parameters and builds a few 
                              dictionaries for positioning/removing labels and arrows.
            change_arrow    | updates the text displayed next to an arrow as well as the arrow's
                              direction and visbility based on some logical conditions
            set_vector_type | overrides the vector_type specified by the class in order to draw 
                              arrows of a different colour.
            set_fill_colour | sets fill colour of self.canvas to specified colour, 
                              or vector type colour as default.
            node_1          | returns the position of the start node of the circuit element
            node_2          | returns end node as above (placeholder)
            draw            | draws the circuit component (placeholder)
            finish_draw     | completes the drawing process by placing arrows and labels after the
                              circuit component has been drawn.
                            
Subclasses for Individual Components:
resistor, voltage, ac_voltage, capacitor, inductor, switch

Subclass Methods:
__init__ | calls parent __init__ to handle most aspects, and adds component-specific code afterwards
draw     | each component draws its circuit symbol through the draw method, then calls parent finish_draw
            
Miscellaneous Functions:
line            | Draws a line between two nodes. No object is created

Example usage:
r1 = resistor(canvas1,1000,  [8,4],  0,    ["R1: 1k","above","",True], ["","below","left","#bb2828",False])
args: (self,  canvas, value, pos,    vert, label_args,                 arrow_args):
        label_args[text(str), position(str), colour(str), display(bool)]
        arrow_args[text(str), position(str), direction(str), colour(str), display(bool)]
        
line(self.canvas1, self.v1.node1(), self.r1.node1())

Usage tips:
Call draw method after changing any parameter of a component object
There are several ways to hide labels/arrows: Set label_args[3] or arrow_args[4] (display(bool)) to False
  or set label_args[1]/arrow_args[1] (position(str)) to "none". Text strings can also be set to "". The first
  might best be used with a global "enable arrows" button whereas inidivudal arrows to hide (i.e. zero voltage
  drop) can be adjusted by setting the position (possibly through change_arrow() method).
"""

import draw
from draw import new_arrow
from physics import vector3
from math import pi

# Important definition so that directions and placements can easily be inverted
opp_dict = {"left":"right", "right":"left", "above":"below", "below":"above", "up":"down", "down":"up", "none":"none"}

class circuit():
  """This class stores components, nodes and lines to be drawn in a given circuit."""
  def __init__(self, canvas, components = dict(), nodes = dict(), lines = set()):
    self.canvas = canvas
    
    # Initialising containers
    self.components = dict() # of components
    self.nodes = dict()     # of str:list
    self.lines = set()      # of tuples
    
    # Adding elements using methods defined below
    if type(components) == dict and type(nodes) == dict and type(lines) == set:
      for i in components:
        # Component type handling in add method
        self.add(i, components[i]) # Name (str) and component
      for i in nodes:
        self.add_node(nodes[i][0], nodes[i][1], i) # x, y, name arguments in this context
        # when calling manually name can be omitted, but dict entries must have keys
      for i in lines:
        self.add_line(i)
    else:
      raise TypeError, "Enter components and nodes as dicts; lines as a set."
      
    # Click checking - adds .clicked attribute to components and maintains in a set
    self.clear_clicks() # Effectively creates the empty set.
    self.draw_currents_if_clicked = True # Default behaviour
    
    # Equivalent resistors: data structure
    # each R_eq corresponds to a set of components
    # also have a function to determine position of R_eq
    # access list of equivalent resistors from self.reqs.keys() or set(self.reqs.keys())
    self.reqs = dict() # format: r_eq1 (resistor object) : {r1, r2, ..., rn} (resistor objects)
    self.draw_equivalent_resistor = True # default
    
    
  # Defining how the object is represented in text
  def __repr__(self):
    return "Circuit object of %i components" % self.count_comps()
  def __str__(self):
    return "Circuit object of %i components" % self.count_comps()
    
  # Utility Methods
  def count_comps(self, comp_type = None):
    """Counts instances of components of a certain type, or all components if type unspecified."""
    if comp_type == None:
      return len(self.components)
    else:
      count = 0
      for i in self.components.values():
        if isinstance(i, comp_type):
          count += 1
      return count
      
  def size(self):
    """Returns a tuple of greatest x and y positions of circuit. Checks components and nodes."""
    comp_max = max(i.node2()[0] for i in self.components.values()) # Assumes node2 is always furthest right
    node_max = max(self.nodes[i][0] for i in self.nodes) # Specified nodes could also be further out than components
    xmax = max(comp_max, node_max)
    
    comp_max = max(i.node2()[1] for i in self.components.values())
    node_max = max(self.nodes[i][1] for i in self.nodes)
    ymax = max(comp_max, node_max)
    return (xmax, ymax)
  
  def clear(self):
    """Resets components, nodes and lines of circuit to empty sets/dicts."""
    self.components = dict()
    self.lines = set()
    self.nodes = dict()
    self.clear_clicks()
    self.clear_reqs()
    
  def clear_clicks(self):
    """Reverts all components to unclicked state."""
    self.clicked = set()
    for i in self.components.values():
      i.clicked = False
      
  def clear_reqs(self):
    """Removes all keys and values in self.reqs dictionary."""
    self.reqs = dict()
    
  
  # Methods for adding to and removing from containers
  # -- For components
  def add(self, name, comp):
    """Adds a component to the circuit."""
    if not isinstance(comp, component):
      raise TypeError, "Object must be of base class component."
    if type(name) != str:
      raise TypeError, "Name of component must be a string."
    else:
      self.components.update({name:comp})
  
  def remove(self, name):
    """Removes a component from the circuit. Does nothing if component isn't in the circuit to begin with."""
    if type(name) != str:
      raise TypeError, "Name of component must be string."
    elif name in self.components:
      self.components.pop(name, None)
      
  def add_req(self, req, r_set = set()):
    """Adds an equivalent resistor object to the dictionary self.reqs."""
    if type(req) != resistor:
      raise TypeError, "Equivalent resistor must be of resistor class."
    if type(r_set) != set:
      raise TypeError, "Resistors must be specified in a set."
    for i in r_set:
      if type(i) != resistor:
        raise TypeError, "All elements of resistor set must be of resistor class."
    # Will overwrite if there is a conflict.
    self.reqs.update({req:r_set})
        
  def remove_req(self, req):
    """Removes an equivalent resistor from the dictionary self.reqs."""
    if type(req) != resistor:
      raise TypeError, "Equivalent resistor must be of resistor class."
    # Will not complain if req not in dictionary.
    self.reqs.pop(req, None)
     
  def toggle_click(self, comp):
    """Toggles a components membership of the self.clicked set."""
    if not isinstance(comp, component):
      raise TypeError, "Object must be of base class component."
    if comp not in self.clicked: # Must be added
      comp.clicked = True
      self.clicked.add(comp)
    else: # Must be removed
      comp.clicked = False
      self.clicked.remove(comp)
    
  # -- For nodes
  def add_node(self, x, y, name = None):
    # needs work.
    """Adds a node to the circuit from which lines can be drawn. Nodes stored in a set."""
     # Generic incrementing ID chosen for name if unspecified
    name = "node_" + str(len(self.nodes)+1) if name == None else name
    self.nodes.update({name:[x,y]}) # Overwrites without error if a pre-existing key is used

  def remove_node(self, argument):
    """Removes a node from the circuit. Can be called by key or value in dict."""
    if type(argument) == str: # Calling by key
      for i in self.nodes:
        if i == argument:
          self.nodes.pop(i, None)
    elif type(argument) == list: # Calling by value
      for i in self.nodes:
        if self.nodes[i][0] == argument[0] and self.nodes[i][1] == argument[1]:
          self.nodes.pop(i, None)
    else:
      raise TypeError, "Argument must be node name as string or position of node as tuple."
      
  # -- For lines
  def add_line(self, start_node, end_node = tuple()):
    """Adds a line to the circuit."""
    if type(start_node) == type(end_node) == tuple:
      if len(start_node) == 4:
        self.lines.add(start_node) # Specifying all 4 co-ords in first argument
      elif len(start_node) == len(end_node) == 2:
        self.lines.add(start_node + end_node) # Concatenating tuples
        # In either case the set element will be of the form (x1,y1,x2,y2)
      else:
        raise KeyError, "Specify two tuples of length 2 or one tuple of length 4."
    else:
      raise TypeError, "Nodes must be tuples."
      
  def remove_line(self, start_node, end_node = []):
    """Removes a line from the circuit."""
    if type(start_node) == type(end_node) == list:
      if len(start_node) == 4 and end_node == []:
        self.lines.discard(start_node) # Removes if present, otherwise does nothing
      elif len(start_node) == len(end_node) == 2:
        self.lines.discard(start_node + end_node) # List concatenation again
      else:
        raise KeyError, "Specify two tuples of length 2 or one tuples of length 4."
    else:
      raise TypeError, "Nodes must be tuples."
    
  
  # Graphical functions  
  def draw(self):
    for i in self.lines:
      line(self.canvas, i[0:2], i[2:4])
      
    for i in self.components.values():
      i.draw()
      if i.clicked and self.draw_currents_if_clicked == True:
        i.draw_current() # guesses direction, specify additional arg here if necessary
        
    if self.draw_equivalent_resistor == True:
      for i in self.reqs:
        if self.reqs[i] == self.clicked: # clickset matches that of req
          i.draw_equivalent()
          if self.draw_currents_if_clicked == True:
            i.draw_current()
      
    
    

class component(): # Base class
  def __init__(self, canvas, value=0, pos=[0,0], vert=0, label_args=["","none","",True], arrow_args=["","none","","",False]):
    self.canvas     = canvas
    self.value      = value
    self.pos        = pos
    self.vert       = vert
    self.label_args = label_args
    self.arrow_args = arrow_args
    
    # Making dictionary mappings for positioning.
    # True mapped to default case, false mapped to none or opposite.
    # l refers to labels, a refers to arrows
    self.l_display_dict    = {True:self.label_args[1], False:"none"}
    self.a_display_dict    = {True:self.arrow_args[1], False:"none"}
    self.a_direction_dict  = {True:self.arrow_args[2], False:opp_dict[self.arrow_args[2]]} # specifies default direction
  
  def change_arrow(self, text="", condition_display=False, condition_direction=True):
    """Updates the text displayed next to an arrow as well as the arrow's direction and visbility.
    If condition_display evaluates True, arrow will be displayed in default position.
    Otherwise the position will be set to "none" and it will not be displayed.
    If condition direction is True, the default arrow direction is used.
    Otherwise the opposite of this direction is used.
    These mappings rely on the dictionaries defined earlier.
    """
    self.arrow_args[0] = text # Set arrow label
    self.arrow_args[1] = self.a_display_dict[condition_display] # Display in position if true, else hide
    self.arrow_args[2] = self.a_direction_dict[condition_direction] # Def. direction if true, reverse if false
    
  def set_vector_type(self, new_type):
    """Use this method to overrule the default vector type used in drawing arrows on components
    E.g. to display an arrow of nonstandard colour (but still one defined in colour_dict in new_arrow)
    Updates only arrow colour and not arrow label, which can be changed by other means."""
    for element in self.dic_a2:
      self.dic_a2[element][0].vector_type = new_type
      
  def set_fill_colour(self, colour = ""):
    """Sets fill colour of self.canvas to specified colour, or vector type colour as default.
    Can be called as simply set_fill_colour() for defaults.
    Colour as 6-digit hex string of form "#aabbcc".    """
    if colour != "":
      self.canvas.fill_style = colour
    else:
      # Must call new_arrow to access colour_dict
      # Creates dummy arrow, while preserving line width
      previous_line_width = self.canvas.line_width
      vector_type = self.dic_a2.values()[0][0].vector_type # Takes it from first dict entry
      new_arrow(self.canvas, vector3(1,0,0,vector_type), -1000, -1000)
      self.canvas.line_width = previous_line_width
      
  def node1(self): 
    """Returns position of start node of component. Is equivalent to self.pos."""
    # No need to overwrite in subclasses
    return tuple(self.pos)

  def node2(self): # Placeholder
    # Should be overwritten in subclasses, because each component has a different shape
    pass
  
  def draw(self): # Placeholder
    # Should be overwritten in subclasses, because each component has a different shape
    pass
  
  def finish_draw(self):
    """Finishes drawing process by placing arrows and labels after the circuit component is drawn.
    This method is called by the draw methods of component subclasses and is not designed to be
    called by itself.    
    """
    can = self.canvas  # Aliasing for readability
    [x, y] = [20*self.pos[0], 20*self.pos[1]]
    
    can.font         = "14px sans-serif"                    # Setting font
    self.textspace   = can.measure_text(self.label_args[0]) # Determining size of labels
    self.textspace_a = can.measure_text(self.arrow_args[0])
    
    # Adding labels
    if self.label_args[3] == True and self.label_args[1] != "none":  
      # Star operator expands list into arguments in the function call
      can.font    = "14px sans-serif" # Setting font
      # Setting label colour, will revert to vector colour if unspecified
      self.set_fill_colour(self.label_args[2]) 
      can.fill_text(self.label_args[0], *self.dic_l[self.label_args[1]])
      
    # Adding arrows
    if self.arrow_args[4] == True:
      self.set_fill_colour(self.arrow_args[3])  # Updates for text only
      can.fill_text(self.arrow_args[0], *self.dic_a1[self.a_display_dict[True]]) # draws arrow label
      if self.arrow_args[2] != "none":
        old_line_width = can.line_width # Preserving line width after possible modification by arrow()
        new_arrow(can, *(self.dic_a2[self.arrow_args[1] + self.arrow_args[2]]))   # draws arrow based on dictionary lookup
        can.line_width = old_line_width
        
  def draw_current(self, direction = None):
    # Calibrated for resistor display but can be called for any component object
    # Currently only supports left and down arrows
    olw = self.canvas.line_width
    if direction == None: # tries to decide for itself
      if self.vert == 0:
        direction = "left"
      else:
        direction = "down"
        
    if direction == "left": # Comes left out of resistor node 1
      vect = vector3(-30, 0, 0, "acceleration")
      new_arrow(self.canvas, vect, 20*self.node1()[0], 20*self.node1()[1])
      self.canvas.fill_style = "#4c7fbe"
      mt = self.canvas.measure_text(self.i)
      
      # Preventing overlap with label on resistor
      if self.label_args[3] and self.label_args[1] == "above":
        mt_r = self.canvas.measure_text(self.label_args[0])
      elif self.arrow_args[4] and self.arrow_args[1] == "above":
        mt_r = self.canvas.measure_text(self.arrow_args[0])
      else:
        mt_r = -1000
      overlap = mt_r/2 + mt/2 - 43
      overlap = overlap * (overlap > 0)
      
      self.canvas.fill_text(self.i, 20*self.node1()[0]-15-mt/2-overlap, 20*self.node1()[1]-20)
      
    elif direction == "down":
      vect = vector3(0, 30, 0, "acceleration")
      new_arrow(self.canvas, vect, 20*self.node2()[0], 20*self.node2()[1])
      self.canvas.fill_style = "#4c7fbe"
      mt = self.canvas.measure_text(self.i)
      self.canvas.fill_text(self.i, 20*self.node2()[0]+10, 20*self.node2()[1]+19)
      
    self.canvas.line_width = olw  
        
  
    
class resistor(component):
  def __init__(self, canvas, value=0, pos=[0,0], vert= 0, label_args=["","none","",True], arrow_args=["","none","","",False]):
    # Inheriting generic component initialisation procedure
    component.__init__(self, canvas, value, pos, vert, label_args, arrow_args)
    
    if value < 0: # Resisor-specific code
      raise "Resistance must be positive."
    
    # Arrow positioning dictionary placed here to reduce workload in draw()
    [x, y] = [20*self.pos[0], 20*self.pos[1]]
    self.dic_a2 = {"aboveright":[vector3(60,0,0,"resistance"), x, y-16], "aboveleft":[vector3(-60,0,0,"resistance"), x+60, y-16],
                   "belowright":[vector3(60,0,0,"resistance"), x, y+16], "belowleft":[vector3(-60,0,0,"resistance"), x+60, y+16],
                   "leftup":[vector3(0,-60,0,"resistance"), x-18, y+60], "leftdown":[ vector3(0,60,0,"resistance"), x-18, y],
                   "rightup":[vector3(0,-60,0,"resistance"), x+18, y+60],"rightdown":[vector3(0,60,0,"resistance"), x+18, y]}  
  def node2(self):
    if self.vert:
      return (self.pos[0], self.pos[1]+3)
    else:
      return (self.pos[0]+3, self.pos[1])
    
  def clicked_resistor(self, x, y):
    '''Returns true if x,y coords are within resistor shape, false otherwise.'''
    if self.vert == False:
      if 20*self.pos[0] < x < 20*self.pos[0] + 60:
        if 20*self.pos[1] - 10 < y < 20*self.pos[1] + 10:
          return True
    elif self.vert == True:
      if 20*self.pos[0] - 10 < x < 20*self.pos[0] + 10:
        if 20*self.pos[1] < y < 20*self.pos[1] + 60:
          return True
        
    return False
  
  
  def draw(self):
    # Aliasing for readability
    can = self.canvas                           
    [x, y] = [20*self.pos[0], 20*self.pos[1]]
    
    # Determining size of labels
    textspace   = can.measure_text(self.label_args[0]) 
    textspace_a = can.measure_text(self.arrow_args[0])
    
    ## Drawing circuit symbol
    can.stroke_style = "#000000" # white fill, black outline
    can.fill_style   = "#ffffff"
    if self.vert == False: 
      can.fill_rect(x, y-10,60,20)
      can.stroke_rect(x, y-10,60,20)
    else:
      can.fill_rect(x-10,y,20,60)
      can.stroke_rect(x-10,y,20,60)      
      
    ## Updating label positions with measured text
    self.dic_l = {"above":[x-textspace/2+30, y-16], "below":[x-textspace/2+30, y+26], 
                  "left":[x-textspace-16, y+35],    "right":[x+16, y+35]}

    ## Updating arrow positions with measured text
    self.dic_a1 = {"above":[x+30-textspace_a/2, y-24], "below":[x+30-textspace_a/2, y+34],
                   "left":[x-25-textspace_a, y+35], "right":[x+25, y+35]}
    # self.dic_a2 is defined in __init__ for performance reasons
      
    # The following graphical commands are common to all components  
    self.finish_draw()
    
  def draw_equivalent(self): # Special commands for when it is an equivalent resistor
    # Aliasing for readability
    can = self.canvas                           
    [x, y] = [20*self.pos[0], 20*self.pos[1]]
    
    # Determining size of labels
    textspace   = can.measure_text(self.label_args[0]) 
    textspace_a = can.measure_text(self.arrow_args[0])
    
    ## Drawing circuit symbol
    can.stroke_style = "#000000" # white fill, black outline
    can.fill_style   = "#ffffff"
    if self.vert == False: 
      can.fill_rect(x, y-10,60,20)
      can.stroke_rect(x, y-10,60,20)
    else:
      can.fill_rect(x-10,y,20,60)
      can.stroke_rect(x-10,y,20,60)      
      
    ## Updating label positions with measured text
    self.dic_l = {"above":[x-textspace/2+30, y-16], "below":[x-textspace/2+30, y+26], 
                  "left":[x-textspace-16, y+35],    "right":[x+16, y+35]}

    ## Updating arrow positions with measured text
    self.dic_a1 = {"above":[x+30-textspace_a/2, y-24], "below":[x+30-textspace_a/2, y+34],
                   "left":[x-25-textspace_a, y+35], "right":[x+25, y+35]}
    # self.dic_a2 is defined in __init__ for performance reasons
      
    # Req specific code - adapt for vert
    text = "Equivalent Resistor"
    mt = can.measure_text(text)
    can.fill_style = "#000000"
    if self.vert == 0:
      line(can, self.node1(), [self.node1()[0]-2, self.node1()[1]])
      line(can, self.node2(), [self.node2()[0]+2, self.node2()[1]])
      can.fill_text(text, 20*self.node1()[0]+30-mt/2, 20*self.node1()[1]+42)
    else:
      line(can, self.node1(), [self.node1()[0], self.node1()[1]-2])
      line(can, self.node2(), [self.node2()[0], self.node2()[1]+2])
      can.fill_text(text, 20*self.node1()[0]-mt/2, 20*self.node2()[1]+62) 
      
    # The following graphical commands are common to all components  
    self.finish_draw()
    
    
class voltage(component): # Voltage source
  def __init__(self, canvas, value=0, pos=[0,0], vert=1, label_args=["","none","",True], arrow_args=["","none","","",False]):  
    # Inheriting generic component initialisation procedure
    component.__init__(self, canvas, value, pos, vert, label_args, arrow_args)
    
    [x, y] = [20*self.pos[0], 20*self.pos[1]]
    self.dic_a2 = {"aboveright":[vector3(60,0,0,"source voltage"), x-20, y-20], "aboveleft":[vector3(-60,0,0,"source voltage"), x+40, y-20],
                   "belowright":[vector3(60,0,0,"source voltage"), x-20, y+18], "belowleft":[vector3(-60,0,0,"source voltage"), x+40, y+18],
                   "leftup":[vector3(0,-60,0,"source voltage"), x-18, y+45], "leftdown":[ vector3(0,60,0,"source voltage"), x-18, y],
                   "rightup":[vector3(0,-60,0,"source voltage"), x+18, y+45],"rightdown":[vector3(0,60,0,"source voltage"), x+18, y]}
  
  def node2(self):
    if self.vert:
      return (self.pos[0], self.pos[1]+1)
    else:
      return (self.pos[0]+1, self.pos[1])
    
  def draw(self):
    can = self.canvas
    [x, y] = [20*self.pos[0], 20*self.pos[1]]
    textspace   = can.measure_text(self.label_args[0])
    textspace_a = can.measure_text(self.arrow_args[0])
    
    ## Circuit symbol
    can.stroke_style = "#000000" # black line
    if self.vert == True:
      can.stroke_rect(x-15, y+5,  30, 0) # long line
      can.stroke_rect(x-7,  y+15, 14, 0) # short line
      can.stroke_rect(x,  y+15, 0, 5) 
      can.stroke_rect(x,  y, 0, 5) 
    else:
      can.stroke_rect(x+5,  y-7, 0, 14)
      can.stroke_rect(x+15, y-15, 0, 30)
      can.stroke_rect(x, y, 5, 0)
      can.stroke_rect(x+15, y, 5, 0)
    
    ## Labels
    self.dic_l = {"above":[x-textspace/2+10, y-20], "below":[x+10-textspace/2, y+30], 
                    "left":[x-textspace-22, y+15],    "right":[x+22, y+15]}
    ## Arrow labels
    self.dic_a1 = {"above":[x-textspace_a/2+10, y-26], "below":[x-textspace_a/2+10, y+34],
                     "left":[x-25-textspace_a, y+15], "right":[x+25, y+15]}
      # remember that self.dic_a2 controls arrow placement and is defined in __init__
      
    self.finish_draw()
   
class ac_voltage(component): # Voltage source
  def __init__(self, canvas, value=0, pos=[0,0], vert=1, label_args=["","none","",True], arrow_args=["","none","","",False]):  
    # Inheriting generic component initialisation procedure
    component.__init__(self, canvas, value, pos, vert, label_args, arrow_args)
    
    [x, y] = [20*self.pos[0], 20*self.pos[1]]
    self.dic_a2 = {"aboveright":[vector3(60,0,0,"source voltage"), x-10, y-17], "aboveleft":[vector3(-60,0,0,"source voltage"), x+50, y-17],
                   "belowright":[vector3(60,0,0,"source voltage"), x-10, y+15], "belowleft":[vector3(-60,0,0,"source voltage"), x+50, y+15],
                   "leftup":[vector3(0,-60,0,"source voltage"), x-15, y+50], "leftdown":[ vector3(0,60,0,"source voltage"), x-15, y-10],
                   "rightup":[vector3(0,-60,0,"source voltage"), x+15, y+50],"rightdown":[vector3(0,60,0,"source voltage"), x+15, y-10]}
  
  def node2(self):
    if self.vert:
      return (self.pos[0], self.pos[1]+2)
    else:
      return (self.pos[0]+2, self.pos[1])
  
  def draw(self):
    can = self.canvas
    [x, y] = [20*self.pos[0], 20*self.pos[1]]
    textspace   = can.measure_text(self.label_args[0])
    textspace_a = can.measure_text(self.arrow_args[0])
    
    ## Circuit symbol
    can.stroke_style = "#000000" # black line
    can.fill_style = "#ffffff"
    if self.vert == True:
      can.begin_path()
      can.arc(x,y+5,5)
      can.fill()
      can.stroke()
      can.begin_path()
      can.arc(x,y+35,5)
      can.fill()
      can.stroke()
    else:
      can.begin_path()
      can.arc(x+5,y,5)
      can.fill()
      can.stroke()
      can.begin_path()
      can.arc(x+35,y,5)
      can.fill()
      can.stroke()
      
    ## Labels
    self.dic_l = {"above":[x-textspace/2+20, y-14], "below":[x-textspace/2+20, y+24], 
                    "left":[x-textspace-14, y+25],    "right":[x+14, y+25]}
    ## Arrow labels
    self.dic_a1 = {"above":[x-textspace_a/2+20, y-26], "below":[x-textspace_a/2+20, y+34],
                     "left":[x-25-textspace_a, y+25], "right":[x+25, y+25]}
      # remember that self.dic_a2 controls arrow placement and is defined in __init__
      
    self.finish_draw()
      
  
  
class capacitor(component):
  # Arrow placements and geometry reproduce those of the voltage source
  def __init__(self, canvas, value=0, pos=[0,0], vert=1, label_args=["","none","",True], arrow_args=["","none","","",False]):  
    # Inheriting generic component initialisation procedure
    component.__init__(self, canvas, value, pos, vert, label_args, arrow_args)
    
    if value < 0:
      raise "Capacitance can't be negative."
    
    [x, y] = [20*self.pos[0], 20*self.pos[1]]
    
    self.dic_a2 = {"aboveright":[vector3(60,0,0,"capacitance"), x-20, y-20], "aboveleft":[vector3(-60,0,0,"capacitance"), x+40, y-20],
                   "belowright":[vector3(60,0,0,"capacitance"), x-20, y+18], "belowleft":[vector3(-60,0,0,"capacitance"), x+40, y+18],
                   "leftup":[vector3(0,-60,0,"capacitance"), x-18, y+45], "leftdown":[ vector3(0,60,0,"capacitance"), x-18, y],
                   "rightup":[vector3(0,-60,0,"capacitance"), x+18, y+45],"rightdown":[vector3(0,60,0,"capacitance"), x+18, y]}
  
  def node2(self):
    if self.vert:
      return (self.pos[0], self.pos[1]+1)
    else:
      return (self.pos[0]+1, self.pos[1])
  
  def draw(self):
    can = self.canvas
    [x, y] = [20*self.pos[0], 20*self.pos[1]]
    textspace   = can.measure_text(self.label_args[0])
    textspace_a = can.measure_text(self.arrow_args[0])
    
    ## Circuit symbol
    can.stroke_style = "#000000" # black line
    if self.vert == True:
      can.stroke_rect(x-15, y+5,  30, 0) # long line
      can.stroke_rect(x-15,  y+15, 30, 0) # short line
      can.stroke_rect(x,  y+15, 0, 5) 
      can.stroke_rect(x,  y, 0, 5) 
    else:
      can.stroke_rect(x+5,  y-15, 0, 30)
      can.stroke_rect(x+15, y-15, 0, 30)
      can.stroke_rect(x, y, 5, 0)
      can.stroke_rect(x+15, y, 5, 0)
    
    ## Labels
    self.dic_l = {"above":[x-textspace/2+10, y-20], "below":[x+10-textspace/2, y+30], 
                    "left":[x-textspace-22, y+15],    "right":[x+22, y+15]}
    ## Arrow labels
    self.dic_a1 = {"above":[x-textspace_a/2+10, y-26], "below":[x-textspace_a/2+10, y+34],
                     "left":[x-25-textspace_a, y+15], "right":[x+25, y+15]}
      
    self.finish_draw()
    
class inductor(component):
  # positioning and geometry copied heavily from resistor class
  def __init__(self, canvas, value=0, pos=[0,0], vert= 0, label_args=["","none","",True], arrow_args=["","none","","",False]):
    component.__init__(self, canvas, value, pos, vert, label_args, arrow_args)
    
    if value < 0:
      raise "Inductance must be positive."
    
    [x, y] = [20*self.pos[0], 20*self.pos[1]]
    self.dic_a2 = {"aboveright":[vector3(60,0,0,"inductance"), x, y-16], "aboveleft":[vector3(-60,0,0,"inductance"), x+60, y-16],
                   "belowright":[vector3(60,0,0,"inductance"), x, y+16], "belowleft":[vector3(-60,0,0,"inductance"), x+60, y+16],
                   "leftup":[vector3(0,-60,0,"inductance"), x-18, y+60], "leftdown":[ vector3(0,60,0,"inductance"), x-18, y],
                   "rightup":[vector3(0,-60,0,"inductance"), x+18, y+60],"rightdown":[vector3(0,60,0,"inductance"), x+18, y]}
  
  def node2(self):
    if self.vert:
      return (self.pos[0], self.pos[1]+3)
    else:
      return (self.pos[0]+3, self.pos[1])
  
  def draw(self):
    can = self.canvas                           # Aliasing for readability
    [x, y] = [20*self.pos[0], 20*self.pos[1]]
    
    textspace   = can.measure_text(self.label_args[0]) # Determining size of labels
    textspace_a = can.measure_text(self.arrow_args[0])
    
    ## Drawing circuit symbol
    can.stroke_style   = "#000000"
    if self.vert == False: # horizontal case, default
      can.begin_path()
      can.arc(x+10, y+3, 10, pi, 0, False)
      can.arc(x+30, y+3, 10, pi, 0, False)
      can.arc(x+50, y+3, 10, pi, 0, False)
      can.move_to(x, y+5)
      can.close_path()
      can.stroke()
    else: # vertical case
      can.begin_path()
      can.arc(x-3, y+10, 10, -pi/2, pi/2, False)
      can.arc(x-3, y+30, 10, -pi/2, pi/2, False)
      can.arc(x-3, y+50, 10, -pi/2, pi/2, False)
      can.move_to(x-5, y)
      can.close_path()
      can.stroke()
      
    ## Updating label positions with measured text
    self.dic_l = {"above":[x-textspace/2+30, y-16], "below":[x-textspace/2+30, y+26], 
                    "left":[x-textspace-16, y+35],    "right":[x+16, y+35]}

    ## Updating arrow positions with measured text
    self.dic_a1 = {"above":[x+30-textspace_a/2, y-24], "below":[x+30-textspace_a/2, y+34],
                     "left":[x-25-textspace_a, y+35], "right":[x+25, y+35]}
      # recall that self.dic_a2 is defined in __init__
      
    self.finish_draw()

class switch(component):
  def __init__(self, canvas, value=0, pos=[0,0], vert=1, label_args=["","none","",True], arrow_args=["","none","","",False]):  
    # Inheriting generic component initialisation procedure
    component.__init__(self, canvas, value, pos, vert, label_args, arrow_args)
    
    if self.value not in [0,1]: # 0 being open, 1 being closed
      raise "Switch's value property should be set to 0 (open) or 1 (closed)."
    
    [x, y] = [20*self.pos[0], 20*self.pos[1]]
    self.dic_a2 = {"aboveright":[vector3(60,0,0,"source voltage"), x-10, y-17], "aboveleft":[vector3(-60,0,0,"source voltage"), x+50, y-17],
                   "belowright":[vector3(60,0,0,"source voltage"), x-10, y+15], "belowleft":[vector3(-60,0,0,"source voltage"), x+50, y+15],
                   "leftup":[vector3(0,-60,0,"source voltage"), x-15, y+50], "leftdown":[ vector3(0,60,0,"source voltage"), x-15, y-10],
                   "rightup":[vector3(0,-60,0,"source voltage"), x+15, y+50],"rightdown":[vector3(0,60,0,"source voltage"), x+15, y-10]}
  
  def node2(self):
    if self.vert:
      return (self.pos[0], self.pos[1]+2)
    else:
      return (self.pos[0]+2, self.pos[1])
  
  def draw(self):
    can = self.canvas
    [x, y] = [20*self.pos[0], 20*self.pos[1]]
    textspace   = can.measure_text(self.label_args[0])
    textspace_a = can.measure_text(self.arrow_args[0])
    
    ## Circuit symbol
    can.stroke_style = "#000000" # black line
    can.fill_style = "#ffffff"
    if self.vert == True:
      can.begin_path()
      can.arc(x,y+5,5)
      can.fill()
      can.stroke()
      can.begin_path()
      can.arc(x,y+35,5)
      can.fill()
      can.stroke()
      
      # Drawing line of switch
      can.move_to(x,y+30)
      if self.value == 1: # closed switch
        can.line_to(x,y+10)
      elif self.value == 0: # open switch
        can.line_to(x-9,y+11)
      can.stroke()
        
    else:
      can.begin_path()
      can.arc(x+5,y,5)
      can.fill()
      can.stroke()
      can.begin_path()
      can.arc(x+35,y,5)
      can.fill()
      can.stroke()
      
      # Drawing line of switch
      can.move_to(x+10,y)
      if self.value == 1: # closed switch
        can.line_to(x+30,y)
      elif self.value == 0: # open switch
        can.line_to(x+29,y-9)
      can.stroke()
      
    ## Labels
    self.dic_l = {"above":[x-textspace/2+20, y-14], "below":[x-textspace/2+20, y+24], 
                    "left":[x-textspace-14, y+25],    "right":[x+14, y+25]}
    ## Arrow labels
    self.dic_a1 = {"above":[x-textspace_a/2+20, y-26], "below":[x-textspace_a/2+20, y+34],
                     "left":[x-25-textspace_a, y+25], "right":[x+25, y+25]}
      # remember that self.dic_a2 controls arrow placement and is defined in __init__
      
    self.finish_draw()
      
      
    
    
    
def line(canvas, pos1, pos2):
  """Draws a line between two nodes on the 20px grid. pos1 and pos2 are lists where
  [0] specifies the x component and [1] specifies the y component. In the case where
  the two points are aligned on either a horizontal or vertical line, this line is drawn.
  Otherwise, the two points are connected via a vertical line and then a horizontal line
  drawn from the first node, achieved via recursion.
  
  Example usage:
  line(self.canvas1, self.v1.node1(), self.r1.node1()) # top left
  """
  canvas.stroke_style = "#000000" # black line
  if pos1[0] == pos2[0]: # vertical line
    canvas.stroke_rect(20*pos1[0],20*pos1[1],0,20*(pos2[1]-pos1[1]))
  elif pos1[1] == pos2[1]: # horizontal line
    canvas.stroke_rect(20*pos1[0],20*pos1[1],20*(pos2[0]-pos1[0]),0)
  else: # Composite line: splits into two segments and recurses. Vertical line drawn first
    midpos = [pos1[0],pos2[1]]
    line(canvas,pos1,midpos)
    line(canvas,midpos,pos2)
    
def create_req(r_set, arranged, new_circuit, to_click, sf = 0):
  """Returns a resistor object equivalent to a set of other resistors arranged in series or parallel."""
  if type(r_set) != set:
    raise TypeError, "Resistors must be specified in a set."
  for i in r_set:
    if type(i) != resistor:
      raise TypeError, "Resistor set must contain only resistor objects."
  if arranged not in ("series", "parallel"):
    raise "Must specify either 'series' or 'parallel' as arranged argument"
  if type(new_circuit) != circuit:
    raise TypeError, "new_circuit must be a circuit object."
  if type(to_click) != str:
    raise TypeError, "to_click must be a string."
  if type(sf) not in (int, float, long) or sf < 0:
    raise TypeError, "Significant figures must be a non-negative number. Floats will be converted to ints."
  
  # Important note:
  # Since resistor objects are mutable, can't just copy one to another without linking the two.
  
  # Getting most attributes from first item in r_set
  # The ordering of the list returned by list(r_set) seems to be related to the order
  #   in which the objects are instantiated; and in any case is not guaranteed to be
  #   the order in which they are added to the set.
  canvas = list(r_set)[0].canvas
  label_args = []
  arrow_args = []
  for i in range(len(list(r_set)[0].label_args)): # Iterating through list of label_args
    label_args.append(list(r_set)[0].label_args[i])         # Admittedly some of these will be overwritten
  for i in range(len(list(r_set)[0].arrow_args)):
    arrow_args.append(list(r_set)[0].arrow_args[i])
  
  # Calculating resistance
  r_sum = 0
  if arranged == "series":
    for i in r_set:
      r_sum += i.value
    r = r_sum
  elif arranged == "parallel":
    for i in r_set:
      r_sum += float(1)/i.value
    r = float(1)/r_sum
  
  # Preparing text representation to the given s.f.
  # Ends up being of the form u"%.2g Ω" % r
  if sf == 0: 
    # Use lazy default mode when trailing zeroes not desired
    if r == int(r):
      label_args[0] = str(int(r)) + u" Ω"
    else:
      label_args[0] = str(r) + u" Ω"
  else:  
    label_args[0] = ("%." + str(int(sf)) + u"g Ω") % r
  
  arrow_args[4] = True
  
  # Deciding on position
  pos = [0,0]
  # First, check whether all in r_set are similarly orientated.
  # Put more brackets here if problems occur
  if all(i.vert == 1 for i in r_set):
    # All are vertical resistors.
    # Moves rightwards from furthest resistor
    pos[0] = max(k.pos[0] for k in r_set) + 6
    # Gets average y pos. Recall that non-integer positions are absolutely fine
    pos[1] = float(sum(k.pos[1] for k in r_set))/len(r_set)
    vert = 1
  else:
    # At least one horizontal resistor
    pos[0] = float(sum(k.pos[0] for k in r_set))/len(r_set)
    pos[1] = max(k.pos[1] for k in r_set) + 5
    vert = 0
    
  # Checking potentials and currents.
  if list(r_set)[0].arrow_args[0][-2:] == " V": # arrows are displaying p.d.
    # maybe use an all() function here
    if arranged == "series":
      pd = sum(float(i.arrow_args[0][:-2]) for i in r_set)
    else:
      pd = float(list(r_set)[0].arrow_args[0][:-2])
    if sf == 0:
      if pd == int(pd):
        arrow_args[0] = str(int(pd)) + " V"
      else:
        arrow_args[0] = str(pd) + " V"
    else:
      arrow_args[0] = ("%." + str(int(sf)) + "g V") % pd
    
    # multiple assignment.
  else:
    # Don't know how to properly format arrow. Hence disable until manually overwritten.
    arrow_args[4] = False 
    
  if arranged == "series":
    # Possibly poor syntax here; not to familiar with try statements
    try: # Use try because i attribute is not part of default resistor object
      current = list(r_set)[0].i
    except:
      current = 0
  elif arranged == "parallel":
    try:
      current = str(sum(int(a.i[:-3]) for a in r_set)) + " mA"
    except:
      current = 0
   
  # Warning: if conditional expressions are specified e.g. in label_args[3] or arrow_args[4] as display
  #  conditions, the expression will be evaluated and then assigned. In essence dynamic behaviour may
  #  be affected. Bear this in mind when you use this function.
  new_resistor = resistor(canvas, r, pos, vert, label_args, arrow_args)
  new_resistor.v = pd
  new_resistor.i = current
  new_resistor.clicked = False
  new_resistor.new_circuit = new_circuit
  new_resistor.to_click = to_click
  
  
  return new_resistor
  
    
    
  
  
  
     
  
    
