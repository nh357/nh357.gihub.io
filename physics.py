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

#This version 2. Modifications from Nicki Humphry-Baker and Michael Conterio
#in March 2016.
"""Anvil service module for physics objects and methods.

Classes:
vector3 -- 3D vector type with each component and type of vector as an attribute.
complex2 -- complex number type.
ball -- 3D ball with vector attributes and associated methods.
point_source -- subclass of ball which radiates spherical waves.

Functions:
exp2 -- complex exponential function.
disc_convolve -- discrete convolution of two functions.
dfft -- discrete fast fourier transform (inverse not working).
disc_fourier -- calculate normal discrete fourier transform.
disc_inv_fourier -- calculate normal inverse discrete fourier transform.
runge_kutta4 -- numerical integration using 4th order Runge-Kutta method.
num_bisection -- find root of function using numerical bisection method.
num_linear -- find root of function using linear interpolation.
num_newton -- find root of function using Newton-Raphson method.
num_secant -- find root of function using secant method.
diff -- numerical differentiation.
diff_5 -- 5th order numerical differentiation.
"""
import math


class ball():
    """Creates a 3d spherical ball object, with mass, position vector, 
    velocity vector and radius. 
    
    Attributes:
    mass (float) - mass of the ball in kilograms
    radius (float) - radius of ball in meters
    pos (vector3) - position vector of the ball
    vel (vector3) - velocity of the ball
    
    Methods:
    move -- moves ball with velocity of the ball
    zmf_vel -- velocity of calculates zero-momentum frame for 2 balls objects. 
                returns a vector3 object
    momentum -- Calculates the momentum vector
    collide -- Calculates the new velocity vectors of 2 balls when they collide
                either ellastically or completely inelastically.
                Returns 2 vector3 objects.
    collision_check -- checks to see if the balls are colliding.
                Returns a boolean. 
    """

    def __init__(self, mass, radius, x =0, y =0, xsp = 0, ysp = 0):
        self.mass = mass
        self.pos = vector3(x, y)
        self.vel = vector3(xsp, ysp, vector_type = "velocity")
        self.radius = radius

    def move(self,dt):
        #move at current constant velocity
        #dt (float) - time interval
        self.pos = self.pos + self.vel*dt

    def zmf_vel(self, other):
        #zero momentum frame velocity vector
        #other (ball object) - other ball in frame.
        summass = self.mass + other.mass
        return (self.vel*self.mass + other.vel*other.mass)/summass

    def momentum(self):
        #return momentum vector
        return self.vel*self.mass

    def collide(self, other, is_elastic):
        #elastically or completely inelastically collides balls 1 and 2
        #other (ball object) - ball 2
        #is_ellastic - boolean
        #returns new velocities
        
        #postion vector between self and other
        posdif = self.pos - other.pos
        #velocity vector of self with respect to other
        veldif = self.vel - other.vel
        #total mass
        summass = self.mass + other.mass
        
        #When balls collide, they will create an impulse on each other 
        #perpendicular to their poin of contact. To find the normal to point of 
        #contact, find the difference between the centres of the 2 balls. It 
        #will only be velocities along this line which will be affected,
        #allowing us to treat the problem as a head-on collision along this 
        #vector. Velocities tangent to this line will be unaffected. The new
        #normal velocities for an ellastic collision will be given by: 
        # v1_normal = u1_normal*(m1 - m2)/summmass + 2*m2*u2_normal/summass
        # v2_normal = u2_normal*(m1 - m2)/summmass + 2*m1*u1_normal/summass
        #u1_normal is obtained by projecting u1 onto the normalised position
        #difference vector using the dot product.
        if is_elastic:
            v1= self.vel - posdif*(2*other.mass/(summass))*(veldif.dot(posdif)/posdif.mag()**2)
            v2= other.vel - posdif*(-2*self.mass/(summass))*(veldif.dot(posdif)/posdif.mag()**2)
        else:
            #if false, then completely inelastic
            v1 = self.zmf_vel(other)
            v2 = self.zmf_vel(other)

        self.vel = v1
        other.vel = v2

    def collision_check(self, other):
        #check if two balls are touching or overlap. Returns a boolean.
        return ((self.pos - other.pos).mag() <= self.radius + other.radius)

class point_source(ball):
    """Subclass of ball which radiates spherical wavefronts."""
    #speed of light, default speed.
    c= 3e8

    def __init__(self, speed = c, frequency = None, wavelength = None, radius = 0.1, x = 0, y = 0, xsp = 0, ysp = 0):
        """Initialize
        Attributes:
        speed (float) -- wavespeed.
        frequency (float) -- wave frequency.
        wavelength (float) -- wavelength.
        radius (float) -- source radius.
        x (float) -- position x component.
        y (float) -- position y component.
        xsp (float) -- velocity x component.
        ysp (float) -- velocity y component.
        wavefront (float) -- position of wavefront from source
        """
        #This allows the point_source to have all the same attributes as a bal object.
        ball.__init__(self, mass = 0.1,radius = radius, x = x, y = y, xsp = xsp, ysp = ysp)

        #if only two of speed, wavelength or frequency are provided, calculate the third
        if frequency !=None:
            if wavelength !=None:
                self.speed = frequency * wavelength
                self.frequency = frequency
                self.wavelength = wavelength
            self.speed = speed
            self.frequency = frequency
            self.wavelength = speed/frequency
        elif wavelength !=None:
            self.speed = speed
            self.wavelength = wavelength
            self.frequency = speed/wavelength
        else:
            raise "Provide two out of three of speed, wavelength or frequency"

        self.wavefront = 0
        self.mousedown = False
    
    #Not sure what this is supposed to do. Look in app that uses it.    
    def __mul__(self, other):
        return self

    def radiate(self, dt):
        #move wavefront
        self.wavefront += self.speed*dt


class vector3():
    """3D vector object with each component as an attribute and associated methods.

    Attributes:
    x (float) -- x component.
    y (float) -- y component.
    z (float) -- z component.
    vector_type (string) -- what type of vector this represents.

    Methods:
    mag -- magnitude of vector.
    phi -- angle in xy-plane (angle in cylindrical polar coordinates from x-axisx).
    theta -- angle from z-axis (azimuthal angle).
    multi -- (deprecated) multiply vector by scalar.
    norm -- normalised vector.
    phi_rotate -- rotate vector by angle.
    dot -- dot product.
    cross -- cross product.
    str -- formatted string of vector.
    """

    def __init__(self, x, y, z = 0, vector_type = "displacement"):
        self.x = x
        self.y = y
        self.z = z
        self.vector_type = vector_type

    def mag(self):
        #magnitude
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
        
    def phi(self):
        #polar angle in radians, between 0 and pi
        return math.atan2(self.y, self.x)
        
    def theta(self):
        #3d azimuthal angle
        if self.mag() == 0:
            return 0
        else:
            xymag = vector3(self.x, self.y, self.vector_type).mag()
            return math.atan2(xymag, self.z)
            
    #depricated
    def multi(self, a):
        #scalar multiplication
        #a (float) - scalar
        return vector3(a*self.x, a*self.y, a*self.z, self.vector_type)
        
    def norm(self):
        #normalised vector
        mag = self.mag()
        if mag == 0:
            return self
        else:
            return vector3(self.x/mag, self.y/mag, self.z/mag, self.vector_type)

    def phi_rotate(self, angle, origin):
        #returns vector with phi changed by angle in anti-clockwise direction
        #in the xy-plane
        #angle (float) - angle in radians
        #origin (vector3) - vector of origin
        
        #test this a little more
        diff= self - origin
        sin = math.sin(angle)
        cos = math.cos(angle)
        new = vector3(cos*diff.x - sin*diff.y, +sin*diff.x + cos*diff.y, 
                      diff.z, self.vector_type)
        return new + origin

    def __add__(self, other):
        #vector addition
        #other (vector3)
        return vector3(self.x+other.x, self.y+other.y, 
                       self.z+other.z, self.vector_type)

    def __iadd__(self, other):
        #vector addition so that can type vector_1 + vector_2 in the code
        #other (vector3)
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __sub__(self, other):
        #vector subtraction
        #other (vector3)
        return vector3(self.x-other.x, self.y-other.y, 
                       self.z-other.z, self.vector_type)

    def __isub__(self, other):
        #vector subtraction
        #other (vector3)
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self

    def __mul__(self, scalar):
        #scalar multiplication
        #scalar (float)
        return vector3(scalar*self.x, scalar*self.y, 
                       scalar*self.z, self.vector_type)

    def __imul__(self, scalar):
        #scalar multiplication
        #scalar (float)
        self.x *= scalar
        self.y *= scalar
        self.z *= scalar
        return self

    def __rmul__(self, scalar):
        #scalar multiplication, when scalar is not what we were epecting
        #scalar (float)
        return vector3(scalar*self.x, scalar*self.y, 
                       scalar*self.z, self.vector_type)

    def __div__(self, scalar):
        #scalar division, check division by zero. Needs checking
        #scalar (float)
        if scalar is not 0:
            return vector3(self.x/scalar, self.y/scalar, 
                       self.z/scalar, self.vector_type)
        else:
            raise "Division by zero impossible"

    def __idiv__(self, scalarv):
        #scalar division
        #scalar (float)
        if scalar is not 0:
            self.x /= scalar
            self.y /= scalar
            self.z /= scalar
            return self
        else:
            raise "Division by zero impossible"
        
    def dot(self, other):
         #dot produt
        #other (vector 3)
        #dots vector self and other
        return (self.x*other.x+self.y*other.y + self.z*other.z)

    def cross(self,other, vector_answer = "displacement"):
         #cross-product
        #other (vector 3)
        #vector_answer (string) - determines type of vector of the answer.
        #crosses vectors self and other
        return vector3(self.y*other.z- other.y*self.z, 
                       other.x*self.z-self.x*other.z, 
                       self.x*other.y -self.y*other.x, 
                       vector_answer)
                       
    #needs more testing
    def __str__(self):
        return "({0}, {1}, {2})".format(repr(self.x), repr(self.y), repr(self.z)) #"({self.x}, {self.y}, {self.z})".format(self)

class answer_vector(vector3):
    """Combination of a 3D vector object with a "preferred point" for it to act from, and an acceptable area for
    it to act from.
    
    New attributes:
    x_pos (float) -- x position of "ideal" location of start point of arrow
    y_pos (float) -- y position of "ideal" location of start point of arrow
    z_pos (float) -- z position of "ideal" location of start point of arrow
    area_radius(float) -- radius of circle from x,y within which the start position will be marked as "correct"
    vectors_around_polygon (list) -- creating vectors between points in area_list
    area_type(string) -- what type of area (polygon or circle) that defines the acceptable area for the start point of the answer
    area_list(list) -- if area_type = "circle", this contains a single float that gives a radius
                    -- if area_type = "polygon", this contains a list of 2D positions representing the corners
                           of that polygon
    angle_range(float) -- number of radians away a submitted vector can be from the correct answer vector and still be marked as correct
    
    
    Attributes inherited from vector3 class:
    Attributes:
    x (float) -- x component.
    y (float) -- y component.
    z (float) -- z component.
    vector_type(string) -- what type of vector this represents
    
                           
    New methods:
    check_convex_polygon: Checks that the polygon defined by area_list is convex
    point_inside_polygon: Checks if the x,y point given is inside the polygon defined by area_list
    angle_within_range: Checks that the vector passed to it is within angle_range of the correct direction
    angle_to_correct: Returns angle in radians between answer vector and the vector passed to it
    point_inside_circle: Checks if the x,y point passed to it is inside the circle defined by x_pos, y_pos and area_radius
    check_answer: Takes in x,y and a vector, checks answer start position and direction
    
   

    Methods inherited from vector3 class:
    mag -- magnitude of vector.
    phi -- angle in xy plane (angle in cylindrical polar coordinates).
    theta -- angle from z axis (azimuthal angle).
    multi -- (deprecated) multiply vector by scalar.
    norm -- normalised vector. 
    phi_rotate -- rotate vector by angle.
    dot -- dot product.
    cross -- cross product.
    str -- formatted string of vector."""
    
    #Written by Michael C, April 2016
    
    def __init__(self, x, y, z = 0, vector_type = "displacement", vector_sub_type = "", x_pos = 0 , y_pos = 0 , z_pos = 0, area_type = "circle", area_list = [0], angle_range = 0.10):
        
        """Initialize
        Attributes:
        x (float) -- x component of vector
        y (float) -- y component of vector
        z (float) -- z component of vector
        vector_type(string) -- what type of vector this represents
        vector_sub_type(string) - more detail about the type of vector
        x_pos (float) -- x position of start of "perfectly accurately" drawn vector
        y_pos (float) -- y position of start of "perfectly accurately" drawn vector
        z_pos (float) -- z position of start of "perfectly accurately" drawn vector
        area_type(string) -- how is the area in which the start position will be marked as "correct" defined?
        area_list(list) -- if area_type = "circle", this contains a single float
                        -- if area_type = "polygon", this contains a list of 2D positions representing the corners
                           of that polygon
        area_radius -- radius of circle from x,y within which the start position will be marked as "correct"
        vectors_around_polygon -- creating vectors between points in area_list
        """
      
        vector3.__init__(self, x =x, y =y, z=z, vector_type = vector_type)
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.z_pos = z_pos
        self.area_type = area_type
        self.angle_range = angle_range
        
        self.area_list = area_list
        
        if vector_type == "force":
            self.vector_sub_type = vector_sub_type
        else:
            self.vector_sub_type = ""
        
        if self.area_type == "circle":
          self.area_radius = area_list[0]
        elif self.area_type == "polygon":
          if self.area_list[-1] != self.area_list[0]:
            self.area_list.append(self.area_list[0])
          #print "polygon"
          self.vectors_around_polygon = []
          for i in range(len(self.area_list) - 1):
              self.vectors_around_polygon.append(vector3(self.area_list[i+1][0] - self.area_list[i][0], self.area_list[i+1][1] - self.area_list[i][1]))
          #print self.vectors_around_polygon
          
          if self.check_convex_polygon() != True:
            raise "this polygon is not convex"
          else:
            print "polygon convex"
            
    
    def check_convex_polygon(self):
        #print "checking polygon"
        #print self.area_list
        
        #Need to add checking to ensure that area_list has at least three points
        
        cross = self.vectors_around_polygon[0].cross(self.vectors_around_polygon[1])
        if cross.z < 0:
          cross_sign = "negative"
        elif cross.z > 0:
          cross_sign = "positive"
        #else:
          #raise "cross product is zero"
        
        for i in range(1, len(self.vectors_around_polygon) - 1):
          cross = self.vectors_around_polygon[i].cross(self.vectors_around_polygon[i+1])
          if cross_sign == "positive" and cross.z <= 0:
            return 0
          elif cross_sign == "negative" and cross.z >=0:
            return 0
          
        return 1
      
    def point_inside_polygon(self, point_x, point_y):
        vector_to_point = vector3(point_x - self.area_list[0][0], point_y - self.area_list[0][1])
        
        cross = self.vectors_around_polygon[0].cross(vector_to_point)
        if cross.z < 0:
          cross_sign = "negative"
        elif cross.z > 0:
          cross_sign = "positive"
        #else:
          #raise "cross product is zero"
        
        for i in range(1, len(self.vectors_around_polygon)):
          vector_to_point = vector3(point_x - self.area_list[i][0], point_y - self.area_list[i][1])
          
          cross = self.vectors_around_polygon[i].cross(vector_to_point)
          if cross_sign == "positive" and cross.z <= 0:
            return 0
          elif cross_sign == "negative" and cross.z >=0:
            return 0
          
        return 1
      
    def point_inside_circle(self, point_x, point_y):
        vector_to_point = vector3(point_x - self.x_pos, point_y - self.y_pos)
        if vector_to_point.mag() <= self.area_radius:
            return 1
        else:
            return 0
      
    def angle_within_range(self, vector_to_compare):
        angle_to_answer = self.angle_to_correct(vector_to_compare)
        if angle_to_answer <= self.angle_range:
            return 1
        elif 3.141592 - angle_to_answer <= self.angle_range:
            return -1
        else:
            return 0
    
    def angle_to_correct(self, vector_to_compare):
        return math.acos(self.dot(vector_to_compare)/(self.mag()*vector_to_compare.mag()))
    
    def check_answer(self, vector_to_check, x_to_check, y_to_check):
        if self.area_type == "polygon":
            if point_inside_polygon(x_to_check, y_to_check) == 1 and angle_within_range(vector_to_check) == 1:
                return 0
            elif point_inside_polygon(x_to_check, y_to_check) == 1 and angle_within_range(vector_to_check) == -1:
                return -1
            elif point_inside_polygon(x_to_check, y_to_check) == 1:
                return [self.angle_to_correct(vector_to_check),0]
            elif angle_within_range(vector_to_check) == 1:
                vector_to_point = vector3(x_to_check - self.x_pos, y_to_check - self.y_pos)
                return [0,vector_to_point.mag()]
                
                
                
        elif self.area_type == "circle":
            if point_inside_circle(x_to_check, y_to_check) == 1 and angle_within_range(vector_to_check) == 1:
                return 0
            elif point_inside_circle(x_to_check, y_to_check) == 1 and angle_within_range(vector_to_check) == -1:
                return -1
            elif point_inside_circle(x_to_check, y_to_check) == 1:
                return [self.angle_to_correct(vector_to_check),0]
            elif angle_within_range(vector_to_check) == 1:
                vector_to_point = vector3(x_to_check - self.x_pos, y_to_check - self.y_pos)
                return [0,vector_to_point.mag()]
        else:
          raise "Incorrect area type"
        
    def to_dict(self):
        {'x' : self.x, 'y' : self.y, 'z' : self.z, 'vector_type' : self.vector_type , 'vector_sub_type' : self.vector_sub_type, 'x_pos' : self.x_pos , 'y_pos' : self.y_pos , 'z_pos' : self.z_pos, 'area_type' : self.area_type, 'area_list' : self.area_list , 'angle_range' : self.angle_range}

class complex2():
    """Complex number with real and imaginary attributes. VERY EARLY STAGES, UNTESTED."""

    def __init__(self,re, im):
        if not isinstance(re, (int, long, float)) or not isinstance(im, (int, long, float)):
            raise "Arguments are not numbers"
        self.re = re
        self.im = im

    def mag(self):
        #magnitude
        return math.sqrt(self.re**2 + self.im**2)

    def phase(self):
        #polar angle in radians, between 0 and pi
        return math.atan2(self.im, self.re)

    def polar(self):
        #returns the number in polar notation
        return (self.mag(), self.phase())
    
    #def cart_complex(polar_self) - needs creating
        #returns the complex number in cartesian coordinates
        #polar_self complex number in polar notation
        #return ()
        
    def phi_rotate(self, angle):
        #returns vector with phi changed by angle in anti clockwise direction
        #angle (float) - anlge of rotation in radians
        
        sin = math.sin(angle)
        cos = math.cos(angle)
        new = complex2(cos*self.re - sin*self.im, +sin*self.re + cos*self.im)
        return new

    def __abs__(self):
        #magnitude
        return math.sqrt(self.re**2 + self.im**2)
        
    def __add__(self, other):
        #addition
        #Other (Complex2 or float)
        
        #check other is of complex2 type
        if isinstance(other, complex2):
            return complex2(self.re+other.re, self.im+other.im)
        else:
            return complex2(self.re+other, self.im)
            
    def __iadd__(self, other):
        #addition
        #other (float or Complex2)
        if isinstance(other, complex2):
            self.re += other.re
            self.im += other.im
        else:
            self.re += other
        return self

    def __sub__(self, other):
        #subtraction
        #other (float or Complex2)
        if isinstance(other, complex2):
            return complex2(self.re-other.re, self.im-other.im)
        else:
            return complex2(self.re-other, self.im)

    def __isub__(self, other):
        #subtraction
        #other (float or Complex2)
        if isinstance(other, complex2):
            self.re -= other.re
            self.im -= other.im
        else:
            self.re -= other
        return self

    def __mul__(self, other):
        #multiplication
        #other (float or Complex2)
        if isinstance(other, complex2):
            return complex2(other.re*self.re - other.im*self.im, other.re*self.im + other.im*self.re)
        else:
            return complex2(other*self.re, other*self.im)

    def __imul__(self, other):
        #multiplication
        #other (float or Complex2)
        if isinstance(other, complex2):
            self =  complex2(other.re*self.re - other.im*self.im, other.re*self.im + other.im*self.re)
        else:
            self.re *= other
            self.im *= other
        return self

    def __rmul__(self, other):
        #multiplication
        #other (float or Complex2)
        return complex2(other*self.re, other*self.im)

    def __div__(self, other):
        #division
        #other (float or Complex2)
        if not isinstance(other, complex2):
            if other == 0:
                raise "Cannot divide by zero"
            else:
                return complex2(self.re/other, self.im/other)
        else:
            if other.mag() == 0:
                raise "Cannot divide by zero"
            else:
                real = (self.re*other.re + self.im*other.im)/(other.re**2 + other.im**2)
                imaginary = (self.im*other.re - self.re*other.im)/(other.re**2 + other.im**2)
                return complex2(real, imaginary)

    def __idiv__(self, other):
        #division
        #other (float or Complex2)
        if not isinstance(other, complex2):
            if other == 0:
                raise "Cannot divide by zero"
            else:
                self.re /= other
                self.im /= other
                return self
        else:
            if other.mag() == 0:
                raise "Cannot divide by zero"
            else:
                real = (self.re*other.re + self.im*other.im)/(other.re**2 + other.im**2)
                imaginary = (self.im*other.re - self.re*other.im)/(other.re**2 + other.im**2)
                return complex2(real, imaginary)

    def __str__(self):
        return "%s + %s i" % (self.re, self.im)

def exp2(x):
    """Return complex exponential, if x not complex use normal exponential function.
    """
    if isinstance(x, complex2):
        return math.exp(x.re)*complex2(math.cos(x.im), math.sin(x.im))
    else:
        return complex2(math.exp(x), 0)

def disc_convolve(f, g):
    """Return discrete convolution list of two discrete function iterables f and g.
    """
    #f (list)
    #g (list)
    result = []
    for i in range(len(f)):
        sums = 0
        for j in range(len(g)):
            if i>=j:
                sums += f[i-j]*g[j]
        result.append(sums)
    return result

def dfft(x, s=1, inverse = False):
    """Discrete fast fourier transform using Cooley-Tukey FFT algorithm.
    Uses complex2 type.
    """
    #4/3/16: Modified this function from what Seyon wrote using code from
    #https://rosettacode.org/wiki/Fast_Fourier_transform#Python:_Recursive -NHB
   # Note: The lenght of x must be a power of 2.
       # OUtput must be normalised by sqrt of the length.
    
    #x (list) -- function to transform
    #s (int) -- s = 1 for first interation, subsequent ones are doubled. 
    #               This is needed to normalise final fft.

    inv = -1 if inverse else 1
    
    #Get length of x
    N = len(x)
    #print "N = %s" % (N)
    #print "s= %s" % (s)
    
    
    if N <= 1: 
        #If length of x is 1, check if element is complex, if not convert to  
        #complex2 object
        if isinstance(x[0], complex2):
            return x
        else:
            return [complex2(x[0],0)]
            
    #Check that the N is a power of 2.
    elif N % 2 > 0:
        raise ValueError("Size of x must be a power of 2.")
            
    else: 
        #Split x into even and odd components
        even = dfft(x[0::2], 2*s)
        odd =  dfft(x[1::2], 2*s)
       # print "even = %s" % (','.join(map(str,even)))
        #print "odd = %s" % (','.join(map(str,odd)))
    
        i = complex2(0, 1)
        #print "N2 = %s" % (N)
        #print N//2
        T= [inv*exp2(-2*inv*i*math.pi*k/N)*odd[k] for k in range(N//2)]
       # print "T = %s" % (','.join(map(str,T)))
        
        #combine the two halves
        result = [(even[k] + T[k]) for k in range(N//2)] + \
           [(even[k] - T[k]) for k in range(N//2)]
        #print "result = %s" % (','.join(map(str,result)))
        
        #Normalises the Fast Fourier transform
        if s == 1:
            result = [x/math.sqrt(N) for x in result]
            
        return result


def disc_fourier(x):
    """Normalised discrete fourier transform of x.
    
    x (list) --  Function to transform"""
    
    X  = []
    i = complex2(0, 1)
    N = len(x)
    for k in range(N):
        result = complex2(0,0)
        for n in range(N):
            result += x[n]*exp2(-2*math.pi*i*n*k/N)
            
        #Normalise by square root of N
        X.append(result/math.sqrt(N))
        
    return X

def disc_inv_fourier(X):
    """Normalised inverse discrete fourier transform.
    
    X (list) -- Function to be transformed"""
    
    x  = []
    i = complex2(0, 1)
    N = len(X)
    for n in range(N):
        result = complex2(0,0)
        for k in range(N):
            result += X[k]*exp2(2*math.pi*i*n*k/N)
        #Normalise by square root of N
        x.append(result/math.sqrt(N))

    return x

def runge_kutta4(y, f, t, dt):
    """Return next iteration of function y with derivative f with timestep dt 
    using Runge-Kutta 4th order. Used to solve ordinary differential equations.
    """
    #Not entirely sure these are the correct types
    #y (range) - function
    #f (range) - derivative of y
    #t (int) - initial time
    #dt (int) - time step
    k1 = f(t, y)
    k2 = f(t + dt/2, y + k1*dt/2)
    k3 = f(t + dt/2, y + k2*dt/2)
    k4 = f(t + dt, y + dt*k3)
    y = y + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)
    return y

def num_bisection(function, a, b, iterations):
    """Find root of function with guesses a,b over iterations using bisection.
    """
    #function must be continuous
    #a (float)
    #b (float)
    #iterations (int)
    
    #convert to integer
    iterations  = int(math.sqrt(iterations**2))
    
    #tolerance
    tol = 0.000001
    if a>b:
        a, b = b, a
    c = (a+b)/2.0
    for letter in (a, b, c):
        if function(letter) == 0:
            return letter

    for i in range(iterations-1):
        if function(c)*function(a)>0:
            a = c
        else:
            b = c
        c = (a+b)/2.0
        #test to see if c is a root.
        if function(c) == 0 or -tol <= (a-b)/2 <= tol:
            return c
        elif i == iterations - 1:
            print "Latest guess is a=%s and b=%s." % (a,c)
            raise "No root was found. Try new guesses."

def num_linear(function, a, b, iterations):
    """Find root of function with guesses a,b over iterations using linear interpolation.
    """
    #function must be continuous
    #a (float)
    #b (float)
    #iterations (int)
    
    #convert to integer
    iterations  = int(math.sqrt(iterations**2))
    if a>b:
        a, b = b, a

    for i in range(iterations):
        fa = function(a)
        fb = function(b)
        c =  a - (b-a)/(fb/fa -1)
        new = function(c)

        if new == 0:
            return c
        elif new*function(a)>0:
            a = c
        else:
            b = c
    return c

def num_newton(function, derivative, guess, iterations):
    """Newton-Raphson numerical method.

    Return root of function using it's first derivative with initial guess, over given iterations."""

    c = guess
    for i in range(iterations):
        fc = function(c)
        if fc ==0:
            return c
        c -= fc/derivative(c)
    return c

def num_secant(function, guess1, guess2, iterations, tol = 0.000001):
    """Secant numerical method.

    Return root of function with initial guess1 and guess2, over given iterations."""

    for i in range(iterations):
        print guess1
        f1 = function(guess1)
        f2 = function(guess2)

        if f1 ==0 or -tol <= guess1 - guess2 <= tol:
            return guess1
        elif f2 ==0:
            return guess2
        # elif f1 == f2:
        #     return None

        c = guess1 - f1*(guess1-guess2)/(f1-f2)
        guess2 = guess1
        guess1 = c
    return guess1

def diff(values):
    """Differentiate values numerically."""
    res = []
    for i in range(len(values)-1):
        x1,y1  = values[i]
        x2, y2 = values[i+1]
        if x2 != x1:
            res.append((x1, (y2-y1)/(x2-x1)))

    return res

def diff_5(values):
    """Differentiate values numerically using 5th order method."""
    res = []
    for i in range(2,len(values)-2):
        h = values[i+1][0] - values[i][0]
        y1= values[i+1][1]
        y2= values[i+2][1]
        y_1= values[i-1][1]
        y_2= values[i-2][1]
        if h != 0:
            res.append((values[i][0], (-y2 + 8*y1 - 8*y_1 + y_2)/(12*h)))

    return res
