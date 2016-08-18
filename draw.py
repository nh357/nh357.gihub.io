# Copyright 2015 Seyon Sivarajah
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
#
#This is version 2. Modified by Nicki Humphry-Baker and Michael Conterio in 
#March 2016.
"""Anvil service module for drawing objects and methods, used with the canvas component.

Classes:
slider -- canvas based slider object for anvil apps.

Functions:
reset2 -- scale canvas and move origin to bottom left.
clear_canvas -- clear the canvas.
border -- draw border on canvas.
eq_triangle -- draw equilateral triangle.
circle -- draw a circle.
arrow -- draw standard arrow.
polygon -- draw a regular polygon.
dashed_line -- draw a dashed line.
paths -- draw dashed lines joining list of points.
vel_arrows -- draw velocity arrow on ball object.
cart_arrows -- draw cartesian component arrows of a vector.
wavelength_to_rgb -- convert wavelength to rgb values.
"""
import math
import physics

class slider():
    """Anvil Canvas slider object.

    Create a slider between mini and maxi with indicator of given colour which 
    can take values in steps of stepsize.
    The starting position is given by start.
    Current value is given in the value attribute.
    Default colour is blue (#318fdb). Optional colour must be given in hex string form.
    Minimum canvas height 40px for standard, 50px with indicators.

    Attributes:
    mini (float)-- minimum value of slider.
    maxi (float)-- maximum values of slider.
    stepsize (float)-- steps to move slider by.
    value (float)-- user accesible, current value of slider.
    mousedown (bool)-- is mouse pressed on slider.
    indicator (bool)-- show value under slider.
    maxmin (bool)-- show maximum and minimum values.
    base_colour (string)-- hex colour string of slider.
    enabled (bool)-- is interaction enabled.

    Methods:
    draw -- draw slider on canvas.
    map_mouse -- map canvas mouse events to slider object mouse events.
    mouse_down -- move slider to click position.
    mouse_move -- move slider with mouse if mouse down.
    mouse_up -- stop interaction when mouse up.
    mouse_leave -- stop mouse interaction when mouse leave.

    """

    default_colour = "#318fdb"
    def __init__(self, canvas, mini, maxi, stepsize, start = 0, colour = default_colour):
        """Initialize slider object.

        Parameters:
        canvas (Canvas)-- anvil canvas component to draw on.
        mini (float)-- minimum value of slider.
        maxi (float)-- maximum values of slider.
        stepsize (float)-- steps to move slider by.
        start (float)-- value to start slider at.
        colour (string)-- MUST BE HEX STRING colour of slider.
        """
        if not mini <= start <= maxi:
            raise "Start value not within range specified."
        self.mini = mini
        self.maxi = maxi
        self.stepsize = stepsize
        self.canvas = canvas

        self.cw = canvas.get_width()
        self.ch = canvas.get_height()

        self.range = maxi - mini
        #scale drawing by range of slider and canvas width
        self.scale = float(self.cw) / self.range

        self.value = start

        self.mousedown = False

        self.base_colour = colour
        self.colour = colour

        self.indicator  = True
        self.maxmin = True

        #size of grabber
        self.grabber_side =15
        self.enabled = True

        #map canvas mouse events
        self.map_mouse()
        #first draw
        self.draw()

    def draw(self):
        #First clears the canvas and then draws the slider on it.
        canvas = self.canvas
        self.cw = canvas.get_width()
        self.ch = canvas.get_height()
        
        #reset canvas transforms
        reset2(self.canvas, 1)
        clear_canvas(canvas, "#fff")
        
        #vertical placement of slider line, with top padding of 5 pixels.
        self.centre = self.ch - self.grabber_side/2 -5
        centre = self.centre
        
        #slider text font
        font_size = 14
        font = "{0}px sans-serif".format(int(font_size))

        #if maximum minimum labels enabled
        if self.maxmin:
            mini_str = "{}".format(repr(self.mini))
            maxi_str = "{}".format(repr(self.maxi))

            #find text widths
            mini_size = canvas.measure_text(mini_str)
            maxi_size = canvas.measure_text(maxi_str)
            
            #find the bigger text and store it in maxi_size
            if mini_size > maxi_size:
                mini_size, maxi_size = maxi_size, mini_size
                
            #set horizontal padding to maximum text size + 5
            self.horpad = maxi_size + 5
        else:
            #default side padding of 10px
            self.horpad = 10

        horpad = self.horpad
        #rescale with horizontal padding
        self.scale = (float(self.cw) - 2*horpad)/ self.range

        #draw line from left border + horizontal padding to 
        #right border - horizontal padding in vertical centre of canvas.
        canvas.begin_path()
        canvas.move_to(horpad, centre)
        canvas.line_width = 4
        canvas.line_cap = "round"
        canvas.line_to(self.cw-horpad, centre)
        canvas.shadow_blur = 0
        canvas.stroke_style = "#333333" #line colour isaac dark grey
        canvas.stroke()

        #Draw grabber/indexer, composed of an equilateral triangle and a square
        grabber_side = self.grabber_side
        
        #find centre of triangle in grabber
        triangle_centre = centre - grabber_side*(1+1/math.sqrt(3))/2
        #draw triangle at value
        polygon(canvas, 3, grabber_side, 
               (self.value - self.mini)*self.scale+ horpad, triangle_centre)
        canvas.fill_style = self.colour
        canvas.fill()
        
        #reset transforms
        reset2(self.canvas, 1)
        
        #draw square with shadow
        polygon(canvas, 4, grabber_side, 
               (self.value - self.mini)*self.scale + horpad, centre)
        
        #reduce shadow if mouse pressed
        canvas.shadow_blur = 2 if self.mousedown else 5
        canvas.shadow_color = "black"
        canvas.fill_style = self.colour
        canvas.fill()
        reset2(self.canvas, 1)

         #indicator: value under grabber
        if self.indicator:
            value_str = "{0}".format(repr(self.value))

            canvas.font = font
            #measure text of value to centre it under grabber
            text_width = canvas.measure_text(value_str)

            canvas.fill_style = "#000"
            canvas.shadow_blur = 0
            
            #height of grabber to offset
            height_offset = self.grabber_side*0.5*(1+math.sqrt(3)) + 1.1*font_size
            canvas.translate((self.value - self.mini)*self.scale - \
                    text_width/2 + horpad, centre - height_offset)
            #Scale canvas as fill_text assumes origin is at top left-hand corner,
            #but reset2 places it at bottom left.
            canvas.scale(1, -1)
            canvas.fill_text(value_str, 0, 0)
            reset2(canvas, 1)

        #maxmin labels
        if self.maxmin:
            canvas.font = font

            #min
            canvas.fill_style = "#000"
            canvas.shadow_blur = 0
            height_offset = float(font_size)/2 - 2
            canvas.translate(0, centre- height_offset)
            #Scale canvas as fill_text assumes origin is at top left-hand corner,
            #but reset2 places it at bottom left.
            canvas.scale(1, -1)
            canvas.fill_text(mini_str, 0, 0)
            reset2(canvas, 1)

            #max
            canvas.translate(self.cw - horpad + 5, centre - height_offset)
            canvas.scale(1, -1)
            canvas.fill_text(maxi_str, 0, 0)
            reset2(canvas, 1)

    #Map mouse events onto the slider in the canvas.
    def map_mouse(self):
        canvas = self.canvas
        canvas.set_event_handler("mouse_up", self.mouse_up)
        canvas.set_event_handler("mouse_leave", self.mouse_leave)
        canvas.set_event_handler("mouse_down", self.mouse_down)
        canvas.set_event_handler("mouse_move", self.mouse_move)
    
    #mouse is clicked
    def mouse_down(self, x, y, button, **event_args):
        # x (int) - horizontal position of mouse
        # y (int) - vertical position of mouse
        # button (button) - clicked button
    
        if self.enabled and self.horpad < x < self.cw - self.horpad + 5:#Modified 25/02/16 - NHB. 
                 #If 5 is added, the second if statement was not needed. 
                 #Initially needed it as otherwise, could not reach end of slider.
            self.mousedown = True
            #if x<self.cw/2: Removed 25/02/16 - NHB
            self.value = int(((x -self.horpad)/self.scale + self.mini)/self.stepsize) * self.stepsize
            #else: #Removed 25/02/16 - NHB
                 # self.value = int(1+((x -self.horpad)/self.scale + self.mini)/self.stepsize)*self.stepsize
            self.draw()

    #mosue is moved
    def mouse_move(self, x, y, **event_args):
        # x (int) - horizontal position of mouse
        # y (int) - vertical position of mouse
     
        #mouse position given from top left, need to map it to bottom right.
        y = self.ch - y
        
        if self.enabled:
            xcheck = abs((x-self.horpad) - (self.value-self.mini)*self.scale) <= self.grabber_side
            ycheck = abs(self.centre - y) <= self.grabber_side
            if xcheck and ycheck:
                self.colour = "#{0:x}".format(int(self.base_colour[1:], 16) + 0x202020)
            else:
                self.colour = self.base_colour
            if self.mousedown and self.horpad < x <self.cw - self.horpad + 5: #modified 16/03/16 NHB c.f.above
                #if x < self.cw/2:
                self.value = int(((x -self.horpad)/self.scale + self.mini)/self.stepsize)*self.stepsize
                #else:
                    #self.value = int(1+((x -self.horpad)/self.scale + self.mini)/self.stepsize)*self.stepsize
            self.draw()

    #mouse is unclicked
    def mouse_up(self, x, y, button, **event_args):
        # x (int) - horizontal position of mouse
        # y (int) - vertical position of mouse
        # button (button) - clicked button
        
        self.mousedown = False
        self.draw()

    #mouse left canvas
    def mouse_leave(self, x, y,**event_args):
        # x (int) - horizontal position of mouse
        # y (int) - vertical position of mouse
    
        self.mousedown = False
        self.draw()

class vert_slider():
    """Anvil Canvas slider object.

    Create a slider between mini and maxi with indicator of given colour which 
    can take values in steps of stepsize.
    The starting position is given by start.
    Current value is given in the value attribute.
    Default colour is blue (#318fdb). Optional colour must be given in hex string form.
    Minimum canvas height 40px for standard, 50px with indicators.

    Attributes:
    mini (float)-- minimum value of slider.
    maxi (float)-- maximum values of slider.
    stepsize (float)-- steps to move slider by.
    value (float)-- user accesible, current value of slider.
    mousedown (bool)-- is mouse pressed on slider.
    indicator (bool)-- show value under slider.
    maxmin (bool)-- show maximum and minimum values.
    base_colour (string)-- hex colour string of slider.
    enabled (bool)-- is interaction enabled.

    Methods:
    draw -- draw slider on canvas.
    map_mouse -- map canvas mouse events to slider object mouse events.
    mouse_down -- move slider to click position.
    mouse_move -- move slider with mouse if mouse down.
    mouse_up -- stop interaction when mouse up.
    mouse_leave -- stop mouse interaction when mouse leave.

    """

    default_colour = "#318fdb"
    def __init__(self, canvas, mini, maxi, stepsize, start = 0, colour = default_colour):
        """Initialize slider object.

        Parameters:
        canvas (Canvas)-- anvil canvas component to draw on.
        mini (float)-- minimum value of slider.
        maxi (float)-- maximum values of slider.
        stepsize (float)-- steps to move slider by.
        start (float)-- value to start slider at.
        colour (string)-- MUST BE HEX STRING colour of slider.
        """
        if not mini <= start <= maxi:
            raise "Start value not within range specified."
        self.mini = mini
        self.maxi = maxi
        self.stepsize = stepsize
        self.canvas = canvas

        self.cw = canvas.get_width()
        self.ch = canvas.get_height()

        self.range = maxi - mini
        #scale drawing by range of slider and canvas height
        self.scale = float(self.ch) / self.range

        self.value = start

        self.mousedown = False

        self.base_colour = colour
        self.colour = colour

        self.indicator  = True
        self.maxmin = True

        #size of grabber
        self.grabber_side =15
        self.enabled = True

        #map canvas mouse events
        self.map_mouse()
        #first draw
        self.draw()

    def draw(self):
        #First clears the canvas and then draws the slider on it.
        canvas = self.canvas
        self.cw = canvas.get_width()
        self.ch = canvas.get_height()
        
        #reset canvas transforms
        reset2(self.canvas, 1)
        clear_canvas(canvas, "#fff")
        
        #horizontal placement of slider line, with side padding of 10 pixels.
        self.centre = self.cw - self.grabber_side/2 -10
        centre = self.centre
        
        #slider text font
        font_size = 14
        font = "{0}px sans-serif".format(int(font_size))

        #if maximum minimum labels enabled
        if self.maxmin:
            mini_str = "{}".format(repr(self.mini))
            maxi_str = "{}".format(repr(self.maxi))

            #find text widths
            mini_size = canvas.measure_text(mini_str)
            maxi_size = canvas.measure_text(maxi_str)
            
            #find the bigger text and store it in maxi_size
            if mini_size > maxi_size:
                mini_size, maxi_size = maxi_size, mini_size
                
            #set vertical padding to maximum text size + 5
            self.vertpad = font_size + 5
        else:
            #default top padding of 10px
            self.vertpad = 10

        vertpad = self.vertpad
        #rescale with vertical padding
        self.scale = (float(self.ch) - 2*vertpad)/ self.range

        #draw line from bottom border + vertical padding to 
        #top border - vertical padding in vertical centre of canvas.
        canvas.begin_path()
        canvas.move_to(centre, vertpad)
        canvas.line_width = 4
        canvas.line_cap = "round"
        canvas.line_to(centre, self.ch-vertpad)
        canvas.shadow_blur = 0
        canvas.stroke_style = "#333333" #line colour isaac dark grey
        canvas.stroke()

        #Draw grabber/indexer, composed of an equilateral triangle and a square
        grabber_side = self.grabber_side
        
        #find centre of triangle in grabber
        #triangle_centre = centre - grabber_side*(1+1/math.sqrt(3))/2
        #draw triangle at value
        
        #polygon(canvas, 3, grabber_side, 
        #      triangle_centre, (self.value - self.mini)*self.scale+ vertpad)
        #canvas.fill_style = self.colour
        #canvas.fill()
        
        #reset transforms
        reset2(self.canvas, 1)
        
        #draw square with shadow
        polygon(canvas, 4, grabber_side, 
                centre, (self.value - self.mini)*self.scale + vertpad)
        
        #reduce shadow if mouse pressed
        canvas.shadow_blur = 2 if self.mousedown else 5
        canvas.shadow_color = "black"
        canvas.fill_style = self.colour
        canvas.fill()
        reset2(self.canvas, 1)

         #indicator: value under grabber
        if self.indicator:
            value_str = "{0}".format(repr(self.value))

            canvas.font = font
            #measure text of value to centre it by grabber
            text_width = canvas.measure_text(value_str)

            canvas.fill_style = "#000"
            canvas.shadow_blur = 0
            
            #width of grabber to offset
            width_offset = self.grabber_side*0.5*(1+math.sqrt(3)) + text_width + 5
            canvas.translate(centre - width_offset, (self.value - self.mini)*self.scale - \
                    text_width/2 + vertpad)
            #Scale canvas as fill_text assumes origin is at top left-hand corner,
            #but reset2 places it at bottom left.
            canvas.scale(1, -1)
            canvas.fill_text(value_str, 0, 0)
            reset2(canvas, 1)

        #maxmin labels
        if self.maxmin:
            canvas.font = font

            #min
            canvas.fill_style = "#000"
            canvas.shadow_blur = 0
            width_offset = float(text_width)/2 - 2
            canvas.translate(centre- width_offset, 0)
            #Scale canvas as fill_text assumes origin is at top left-hand corner,
            #but reset2 places it at bottom left.
            canvas.scale(1, -1)
            canvas.fill_text(mini_str, 0, 0)
            reset2(canvas, 1)

            #max
            canvas.translate(centre - width_offset, self.ch - vertpad + 5)
            canvas.scale(1, -1)
            canvas.fill_text(maxi_str, 0, 0)
            reset2(canvas, 1)

    #Map mouse events onto the slider in the canvas.
    def map_mouse(self):
        canvas = self.canvas
        canvas.set_event_handler("mouse_up", self.mouse_up)
        canvas.set_event_handler("mouse_leave", self.mouse_leave)
        canvas.set_event_handler("mouse_down", self.mouse_down)
        canvas.set_event_handler("mouse_move", self.mouse_move)
    
    #mouse is clicked
    def mouse_down(self, x, y, button, **event_args):
        # x (int) - horizontal position of mouse
        # y (int) - vertical position of mouse
        # button (button) - clicked button
    
        if self.enabled and self.vertpad < y < self.ch - self.vertpad + 5:#Modified 25/02/16 - NHB. 
                 #If 5 is added, the second if statement was not needed. 
                 #Initially needed it as otherwise, could not reach end of slider.
            self.mousedown = True
            #if x<self.cw/2: Removed 25/02/16 - NHB
            self.value = int(((y -self.vertpad)/self.scale + self.mini)/self.stepsize) * self.stepsize
            #else: #Removed 25/02/16 - NHB
                 # self.value = int(1+((x -self.horpad)/self.scale + self.mini)/self.stepsize)*self.stepsize
            self.draw()

    #mosue is moved
    def mouse_move(self, x, y, **event_args):
        # x (int) - horizontal position of mouse
        # y (int) - vertical position of mouse
     
        #mouse position given from top left, need to map it to bottom right.
        x = self.cw - x
        
        if self.enabled:
            ycheck = abs((y-self.vertpad) - (self.value-self.mini)*self.scale) <= self.grabber_side
            xcheck = abs(self.centre - x) <= self.grabber_side
            if xcheck and ycheck:
                self.colour = "#{0:x}".format(int(self.base_colour[1:], 16) + 0x202020)
            else:
                self.colour = self.base_colour

            if self.mousedown and self.vertpad < y <self.ch - self.vertpad + 5: #modified 16/03/16 NHB c.f.above
                #if x < self.cw/2:
                self.value = int(((y -self.vertpad)/self.scale + self.mini)/self.stepsize)*self.stepsize
                #else:
                    #self.value = int(1+((x -self.horpad)/self.scale + self.mini)/self.stepsize)*self.stepsize
            self.draw()

    #mouse is unclicked
    def mouse_up(self, x, y, button, **event_args):
        # x (int) - horizontal position of mouse
        # y (int) - vertical position of mouse
        # button (button) - clicked button
        
        self.mousedown = False
        self.draw()

    #mouse left canvas
    def mouse_leave(self, x, y,**event_args):
        # x (int) - horizontal position of mouse
        # y (int) - vertical position of mouse
    
        self.mousedown = False
        self.draw()
        
class log_scale_bar_vert():
    """Anvil Canvas slider object.

    Create a logarithmic scale bar between mini and maxi with indicator of given colour which 
    can take values in steps of stepsize.
    The starting position is given by start.
    Current value is given in the value attribute.
    Default colour is blue (#318fdb). Optional colour must be given in hex string form.
    Minimum canvas height 40px for standard, 50px with indicators.

    Attributes:
    mini (float)-- minimum value of slider.
    maxi (float)-- maximum values of slider.
    stepsize (float)-- steps to move slider by.
    value (float)-- user accesible, current value of slider.
    mousedown (bool)-- is mouse pressed on slider.
    indicator (bool)-- show value under slider.
    maxmin (bool)-- show maximum and minimum values.
    base_colour (string)-- hex colour string of slider.
    enabled (bool)-- is interaction enabled.

    Methods:
    draw -- draw slider on canvas.
    map_mouse -- map canvas mouse events to slider object mouse events.
    mouse_down -- move slider to click position.
    mouse_move -- move slider with mouse if mouse down.
    mouse_up -- stop interaction when mouse up.
    mouse_leave -- stop mouse interaction when mouse leave.

    """

    default_colour = "#509e2e"
    def __init__(self, canvas, mini, maxi, start = 0, colour = default_colour):
        self.enabled = True
        """Initialize slider object.

        Parameters:
        canvas (Canvas)-- anvil canvas component to draw on.
        mini (float)-- minimum value of slider.
        maxi (float)-- maximum values of slider.
        stepsize (float)-- steps to move slider by.
        start (float)-- value to start slider at.
        colour (string)-- MUST BE HEX STRING colour of slider.
        """
        
        self.mini = 10**(math.floor(math.log10(mini)))
        self.maxi = 10**(math.ceil(math.log10(maxi)))
        
        #if not self.mini <= start <= self.maxi:
            #raise "Value not within range specified."
        
        self.canvas = canvas

        self.cw = canvas.get_width()
        self.ch = canvas.get_height()

        #Range gives numbers of orders of magnitude
        self.range = math.log10(self.maxi) - math.log10(self.mini)
        
        #scale drawing by range of slider and canvas width
        self.scale = float(self.ch) / self.range

        self.value = start

        self.mousedown = False

        self.base_colour = colour
        self.colour = colour

        self.indicator  = True
        self.maxmin = True

        #map canvas mouse events
        
        #first draw
        self.draw()

    def draw(self):
        #First clears the canvas and then draws the slider on it.
        canvas = self.canvas
        self.cw = canvas.get_width()
        self.ch = canvas.get_height()
        
        #reset canvas transforms
        reset2(self.canvas, 1)
        clear_canvas(canvas, "#fff")
        
        #horizontal placement of center line, with side padding of 5 pixels.
        self.centre = self.cw/2 -5
        centre = self.centre
        
        #slider text font
        font_size = 14
        font = "{0}px sans-serif".format(int(font_size))

        #if maximum minimum labels enabled
        if self.maxmin:
            mini_str = "{}".format(repr(self.mini))
            maxi_str = "{}".format(repr(self.maxi))

            #find text widths
            mini_size = canvas.measure_text(mini_str)
            maxi_size = canvas.measure_text(maxi_str)
            
            #find the bigger text and store it in maxi_size
            if mini_size > maxi_size:
                mini_size, maxi_size = maxi_size, mini_size
                
            #set vertical padding to maximum text size + 5
            self.vertpad = maxi_size + 5
        else:
            #default top padding of 10px
            self.vertpad = 10

        vertpad = self.vertpad
        #rescale with vertical padding
        self.scale = (float(self.ch) - 2*vertpad)/ self.range

        #draw line from top border + vert padding to 
        #bottom border - vert padding in vertical centre of canvas.
        canvas.begin_path()
        canvas.move_to(centre, vertpad)
        canvas.line_width = 4
        canvas.line_cap = "round"
        canvas.line_to(centre, self.ch-vertpad)
        canvas.shadow_blur = 0
        canvas.stroke_style = "#333333" #line colour isaac dark grey
        canvas.stroke()
        
        canvas.begin_path()
        canvas.move_to(centre-5, vertpad)
        canvas.line_to(centre+5, vertpad)
        canvas.stroke()
        

        
        #indicator: value of bar
        if self.value > self.mini and self.value < self.maxi:
          
        
          
            value_str = "%.3g" %(self.value)

            canvas.font = font
            #measure text of value to centre it under grabber
            text_width = canvas.measure_text(value_str)
            text_height = 1.1 * font_size

            canvas.fill_style = "#000"
            canvas.shadow_blur = 0
            
            #width of font to offset
            width_offset =  text_width + (float(font_size)/2 - 2)
            canvas.translate(centre - width_offset, (math.log10(self.value/self.mini))*self.scale - \
                    text_height/2 + vertpad)
            #Scale canvas as fill_text assumes origin is at top left-hand corner,
            #but reset2 places it at bottom left.
            canvas.scale(1, -1)
            canvas.fill_style = self.colour
            canvas.fill_text(value_str, 0, 0)
            reset2(canvas, 1)
            
            #draw bar
            width_offset = float(font_size)/2 - 2
            canvas.begin_path()
            canvas.move_to(centre-width_offset,vertpad)
            canvas.line_to(centre-width_offset,vertpad + (math.log10(self.value/self.mini))*self.scale)
            canvas.line_to(centre+width_offset,vertpad + (math.log10(self.value/self.mini))*self.scale)
            canvas.line_to(centre+width_offset,vertpad)
            canvas.close_path()
            canvas.fill_style = self.colour
            canvas.fill()
            reset2(canvas, 1)

        #maxmin labels
        if self.maxmin:
            canvas.font = font

            #min
            canvas.fill_style = "#000"
            canvas.shadow_blur = 0
            width_offset = float(font_size)/2 - 2
            text_height = 1.1 * font_size
            canvas.translate(centre+ width_offset, vertpad - text_height/2)
            #Scale canvas as fill_text assumes origin is at top left-hand corner,
            #but reset2 places it at bottom left.
            canvas.scale(1, -1)
            canvas.fill_text(mini_str, 0, 0)
            reset2(canvas, 1)

            #max
            canvas.translate(centre + width_offset, self.ch - vertpad + 5 - text_height/2)
            canvas.scale(1, -1)
            canvas.fill_text(maxi_str, 0,0)
            reset2(canvas, 1)
            
            for i in range(1,int(self.range)):
              canvas.translate(centre+ width_offset, vertpad + (i*self.scale) - text_height/2)
              canvas.scale(1, -1)
              add_str = "{0}".format(self.mini * (10**i))
              canvas.fill_text(add_str, 0,0)
              reset2(canvas, 1)    
            
            
#Start of functions
def reset2(canvas, xu):
    """Custom canvas reset function. Resets canvas, then 
     scales to xu, and places origin at bottom left.
    """
     #canvas (Canvas)
     #xu (int) - scaling factor in pixels
    canvas.reset_transform()
    canvas.translate(0, canvas.get_height())
    canvas.scale(xu,-xu)

def clear_canvas(canvas, colour = "#fff"):
    """Fill canvas with colour.
    """
    canvas.fill_style= colour
    canvas.fill_rect(0, 0, canvas.get_width(), canvas.get_height())

def border(canvas, thickness, colour, xu=1):
    """Draw border of thickness and colour on canvas which has been scaled by xu.
    """
    #canvas (Canvas)
    #thickness (int) - thickness of border in pixels
    #colour (string) - colour of border. MUST BE IN HEX.
    
    canvas.begin_path()
    
    #remove scaling from line_width
    canvas.line_width = thickness/xu
    canvas.stroke_style = colour
    canvas.stroke_rect(0, 0, canvas.get_width()/xu, canvas.get_height()/xu)

#Probably not needed
#def eq_triangle(canvas, side, x= 0, y= 0):
#  """Draw upward equilateral triangle with bottom left corner at x, y."""
#
   # canvas.translate(x,y)
   # canvas.begin_path()
   # canvas.move_to(0,0)
   # canvas.line_to(float(side), 0)
   # canvas.line_to(float(side)/2, math.sqrt(3))
   # canvas.close_path()
    #canvas.translate(-x,-y)

def circle(canvas, radius, x = 0, y = 0):
    """Draw circle of radius at x, y."""

    canvas.begin_path()
    canvas.arc(x, y, float(radius), 0, 2*math.pi)
    canvas.close_path()

def new_arrow(canvas, vector, x= 0, y= 0):
   """Draws an arrow starting at x and y along the vector3 object vector. Draws
   it in the appropriate isaac colours.
   """
   #canvas is the canvas to draw on
   #vector is a vector3 object
   #x and y are the co-ordinates of the start of the arrow
   #type_of_vector is a text string which should be from the list below


   #No zero-length arrows:
   if vector.mag() == 0:
       return 0


   #Work out colour of arrow from vector type
   colour_dict = {"displacement":"#000000",
     "force":"#bb2828",
     "force2": "#fea100",
     "velocity": "#49902a",
     "acceleration":"#4c7fbe",
     "light_grey":"#CCCCCC",
     "dark_grey":"#666666",
     "yellow":"#fea100"}

   if vector.vector_type in colour_dict:
      arrow_colour = colour_dict[vector.vector_type]
   else:
      arrow_colour = "#333333"

   #The tip length of the arrow is 1/10 of the length of the arrow
   arrow_length = vector.mag()

   arrow_tip_length = 0.1 * arrow_length

   if arrow_tip_length < 5:
     arrow_tip_length = 5

   if arrow_length < 3:
     arrow_width = arrow_length
   elif arrow_length < 100:
     arrow_width = 3 + 0.02 * arrow_length
   elif arrow_length < 600:
     arrow_width = 5 + 0.005 * arrow_length
   else:
      arrow_width = 7.5

   print "Vector = %d, arrow_width = %d" %(arrow_length,arrow_width )
   print "Vx = %d, Vy = %d, arrow tip = %d" %(vector.x, vector.y, arrow_tip_length)


   #Work out the angle of the vector to the horizontal
   drawing_arrow_direction = vector.phi()


   #move to corner
   canvas.translate(x,y)
   canvas.begin_path()
   canvas.move_to(0,0)

   # Draw main part of the arrow
   canvas.line_to(vector.x,vector.y)
   canvas.close_path()

   canvas.stroke_style = arrow_colour
   canvas.fill_style = arrow_colour
   canvas.line_width = arrow_width

   canvas.stroke()

   #From end of arrow, draw a triangle for the head of the arrow. The edges are at 0.5236 radians to the direction of the arrow
   canvas.begin_path()
   canvas.move_to(vector.x,vector.y)
   canvas.line_to(vector.x-arrow_tip_length*math.cos(drawing_arrow_direction-0.5236),vector.y-arrow_tip_length*math.sin(drawing_arrow_direction-0.5236))
   canvas.line_to(vector.x-arrow_tip_length*math.cos(drawing_arrow_direction+0.5236),vector.y-arrow_tip_length*math.sin(drawing_arrow_direction+0.5236))
   canvas.close_path()

   #Fill the arrowhead in
   canvas.stroke()
   canvas.fill()

   #Move canvas back
   canvas.translate(-x,-y)

def arrow(canvas, length, width, x= 0, y= 0):
    """Draw horizontal arrow of length and width starting at middle of base at x,y."""
    #Redundant, but needs to be roemoved from existing simulations
    #move to corner
    canvas.translate(x,y+ width/2)
    canvas.begin_path()
    canvas.move_to(0,0)
    #horizontal line
    canvas.line_to(0.8*length, 0)
    #up on arrow head
    canvas.line_to(0.8*length, 1.5*width/2)
    #to tip
    canvas.line_to(length, -width/2)
    #back
    canvas.line_to(0.8*length, -3.5*width/2)
    #finish head
    canvas.line_to(0.8*length, -width)
    #back to base
    canvas.line_to(0, -width)
    canvas.close_path()
    #negate translation
    canvas.translate(-x,-y-width/2)

def polygon(canvas, sides, length, x = 0, y = 0, phi = 0):
    """Draw regular polygon with sides of length, whose centre is at x, y.
    Can be rotated about its centre by phi. Default is 0 radions.
    """
    #Modified by Nicki HB, May 2016
    
    #canvas (Canvas)
    #sides (float) - number of sides of polygon
    #length (float) - lenght of sides
    #x (int) - horizontal position
    #y (int) - veritcal position
    canvas.translate(x,y)
    N = sides
    l = length
    
    #central angle
    a = 2*math.pi/N
    
    #distance from centre to middle of one side
    d = float(l)*math.sqrt((1+math.cos(a))/(1-math.cos(a)))/2
     #Rotates canvas by alpha before drawing. All subsequent points are 
    #rotated by phi too.
    canvas.rotate(phi)
    #Starts the polygon to the left of the centre and down
    canvas.begin_path()
    canvas.move_to(-l/2, d)
    
    #Rotate each subsequent line_to by the central angle.
    for i in range(N):
        canvas.rotate(a)
        canvas.line_to(-l/2, d)
    canvas.close_path()
    
    #Remove rotation and translation
    canvas.rotate(-phi)
    canvas.translate(-x,-y)

def dashed_line(canvas, dashlength, x2, y2, x = 0, y = 0, colour = "black"):
    """Draw dashed line from x, y to x2, y2, each segment of length dashlength.
    """
    #Default colour added by Michael C, April 2016
    
    #canvas (Canvas)
    #dashlength (float) - length of segment
    #x (int) - initial horizontal position
    #y (int) - initial veritcal position
    #x2 (int) - final horizontal position
    #y2 (int) - final veritcal position
    #colour (string) - colour of dashed lines. Default is black
    
    #total length of line
    length = math.sqrt((x2-x)**2 + (y2-y)**2)
    
    #number of dashes.
    no = int(length/dashlength)
    if no>0:
        #x length
        dx= float(x2-x)/no
        #y  length
        dy = float(y2-y)/no
        #fraction of segment to draw (dash size)
        factor = 0.8
        
        canvas.stroke_style = colour
        canvas.begin_path()
        canvas.move_to(x,y)

        for i in range(no):
            canvas.line_to(x+(i+factor)*dx, y+(i+factor)*dy)
            canvas.move_to(x + (i+1)*dx, y + (i+1)*dy)
            
        canvas.stroke()
    else:
        pass


def paths(canvas, paths, thickness, colour = "#333333"):
    """Draw dashed line of colour and thickness joining list of paths.

    Each list in paths must be a list of physics.vector3 types.
    """
    
    #canvas (Canvas)
    #paths (list of physics.vector3 types) - list of vectors
    #thickness (float) - thickness of paths
    #colour (string) - hex colour for paths. defualt is isaac dark grey
    
    canvas.begin_path()
    #for each path
    for path in paths:
        if len(path) > 2:
            for i in range(len(path)-1):
                canvas.move_to(path[i].x, path[i].y)
                diff = path[i+1] - path[i]
                new  = path[i] + diff*0.8
                canvas.line_to(new.x, new.y)

    canvas.line_width = thickness
    canvas.stroke_style = colour
    canvas.stroke()

def cart_arrows(self, canvas, vector, line_width, arrow_scale = 0.15, 
                colours = {'x':"#666666",'y':"#666666",'z':"#666666"}, x= 0, y=0 ):
        """Draw cartesian components of vector (physics.vector3 type) in xyz in approriate 
        colours. Default colour is isaac middle grey. Draws an axes in bottom left."""
        #Modified by Michael Conterio, March 2016
        
        #Draw axis reminder
        canvas.translate(50,50)
        canvas.rotate(math.pi/6 + math.pi)
        canvas.scale(10*line_width, 10*line_width)
        canvas.begin_path()
        #dashed axes
        self.dashed_line(canvas, 0.2, 1,0)
        canvas.line_width = 0.06
        canvas.stroke()
        canvas.scale(0.1/line_width, 0.1/line_width)
        canvas.rotate(-math.pi/6- math.pi)
        
        canvas.scale(10*line_width, 10*line_width)
        canvas.begin_path()
        self.dashed_line(canvas, 0.2,1,0)
        canvas.line_width = 0.06
        canvas.stroke()
        canvas.scale(0.1/line_width, 0.1/line_width)
        
        canvas.rotate(math.pi/2)
        canvas.scale(10*line_width, 10*line_width)
        canvas.begin_path()
        canvas.stroke_style = "#000000"
        self.dashed_line(canvas, 0.2,1,0)
        canvas.line_width = 0.06
        canvas.stroke()
        canvas.scale(0.1/line_width, 0.1/line_width)
        canvas.rotate(-math.pi/2)
        
        canvas.translate(-50,-50)
        
        #z component
        canvas.translate(x, y)
        canvas.rotate(math.pi/6 + math.pi)
        #component arrow
        z_vector = physics.vector3(1,0,0,vector.vector_type)
        self.arrow(canvas, vector.z*vector3(1,0,0,vector.vector_type),0,0)
        canvas.rotate(-math.pi/6- math.pi)
    
        #x component
        self.arrow(canvas, vector.x*vector3(1,0,0,vector.vector_type),0,0)
    
        #y component
        canvas.rotate(math.pi/2)
        self.arrow(canvas, vector.y*vector3(1,0,0,vector.vector_type),0,0)
        canvas.rotate(-math.pi/2)
    
        canvas.translate(-x,-y)
        

def component_arrows(self, canvas, vector, axis_vector = physics.vector3(0,1), 
                        x= 0, y=0, vector_from_start = "both", what_to_draw = "arrow", 
                        colour_parallel = "black",colour_perpendicular = "black"):
    """Draws components of vector parallel and perpendicular to axis_vector, in the x-y plane
    returns a list containing vector3 objects corresponding to the components parallel
    and perpendicular to axis_vector. Default it draws arrow components. Can 
    modifiy to dashed lines by setting what_to_draw = "dashed"
    """
    #Created by Michael C, April 2016
    
    #canvas(canvas) -  canvas to draw on
    #vector(vector3 object) - vector to split into components
    #axis_vector(vector3 object) - vector describing direction of axis components should be given parallel
    #                              or perpendicular to
    #x(float) - x position on canvas from which components should be drawn
    #y(float) - y position on canvas from which components should be drawn
    #vector_from_start(string) - which of the component vectors should be drawn from the given x,y - if not "both", other #will be drawn from end of this component
    #what_to_draw(string) - should these components be drawn as arrows or dashes
    #colour_parallel(string) 
    #colour_perpendicular(string) - colours of these two lines/arrows
    
    if vector.z != 0 or axis_vector.z != 0:
        raise
            
    #canvas.translate(x, y)
    
    #component_parallel to axis_vector:
    parallel_vector = (vector.dot(axis_vector)/(axis_vector.mag()**2)) * axis_vector
    parallel_vector.vector_type = vector.vector_type
    
    perpendicular_vector = vector - parallel_vector
    
    if vector_from_start == "both":
        parallel_vector_start_x = 0
        parallel_vector_start_y = 0
        perpendicular_vector_start_x = 0
        perpendicular_vector_start_y = 0
    elif vector_from_start == "parallel":
        parallel_vector_start_x = 0
        parallel_vector_start_y = 0
        perpendicular_vector_start_x = parallel_vector.x
        perpendicular_vector_start_y = parallel_vector.y
    else:
        parallel_vector_start_x = perpendicular_vector.x
        parallel_vector_start_y = perpendicular_vector.y
        perpendicular_vector_start_x = 0
        perpendicular_vector_start_y = 0
    
    
    if what_to_draw == "arrow":              
      new_arrow(canvas, parallel_vector, parallel_vector_start_x+x, parallel_vector_start_y+y)
      new_arrow(canvas, perpendicular_vector, perpendicular_vector_start_x+x, perpendicular_vector_start_y+y)
    elif what_to_draw == "dashed":      
      dashed_line(canvas, 10, parallel_vector.x + parallel_vector_start_x +x, parallel_vector.y + parallel_vector_start_y+y, x=parallel_vector_start_x+x, y= parallel_vector_start_y+y, colour = colour_parallel)
      dashed_line(canvas, 10, perpendicular_vector.x + perpendicular_vector_start_x+x, perpendicular_vector.y + perpendicular_vector_start_y+y, x=perpendicular_vector_start_x+x, y= perpendicular_vector_start_y+y, colour = colour_perpendicular)
    
    return [parallel_vector, perpendicular_vector]
    
    
def wavelength_to_rgb(wavelength, gamma=0.8):
    '''This converts a given wavelength of light to an
    approximate RGB color value. The wavelength must be given
    in nanometers in the range from 380 nm through 750 nm
    (789 THz through 400 THz).

    Based on code by Dan Bruton
    http://www.physics.sfasu.edu/astro/color/spectra.html
    '''
    #wavelength (int) - wavelength of light
    #gamma (float) - Correction for eye sensitivity
    
    wavelength = float(wavelength)
    if wavelength >= 380 and wavelength <= 440:
        #attenuate as at edge of vision
        attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
        R = ((-(wavelength - 440) / (440 - 380)) * attenuation) ** gamma
        G = 0.0
        B = (1.0 * attenuation) ** gamma
    elif wavelength >= 440 and wavelength <= 490:
        R = 0.0
        G = ((wavelength - 440) / (490 - 440)) ** gamma
        B = 1.0
    elif wavelength >= 490 and wavelength <= 510:
        R = 0.0
        G = 1.0
        B = (-(wavelength - 510) / (510 - 490)) ** gamma
    elif wavelength >= 510 and wavelength <= 580:
        R = ((wavelength - 510) / (580 - 510)) ** gamma
        G = 1.0
        B = 0.0
    elif wavelength >= 580 and wavelength <= 645:
        R = 1.0
        G = (-(wavelength - 645) / (645 - 580)) ** gamma
        B = 0.0
    elif wavelength >= 645 and wavelength <= 750:
        #attenuate as at edge of vision
        attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
        R = (1.0 * attenuation) ** gamma
        G = 0.0
        B = 0.0
    else:
        R = 0.0
        G = 0.0
        B = 0.0
    R *= 255
    G *= 255
    B *= 255
    return (int(R), int(G), int(B))
