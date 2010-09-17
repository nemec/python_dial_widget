import pygtk
pygtk.require('2.0')
import gtk
import StringIO
import gobject
from math import pi, acos, sin
from sys import exit

try:
  import Image
except ImportError:
  print "Error importing module Image. This widget requires the Python Imaging Library."
  print "Please visit http://www.pythonware.com/products/pil/ to download the module."
  exit()

try:
  from numpy import array, dot, cross
  from numpy.linalg import norm
except ImportError:
  print "Error importing module NumPy. This widget requires the Numerical Python Library."
  print "Please visit http://numpy.scipy.org/ to download the module."
  exit()

class Dial(gtk.EventBox):

  __gtype_name__ = "Dial"

  __gsignals__ = {
    # Emitted every time the dial moves up a "notch"
    "dial-increase": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
    # Emitted every time the dial moves down a "notch"
    "dial-decrease": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
    # Emitted every time the dial moves (even a miniscule amount)
    # The event argument is the ticker value as a float to an arbitrary precision
    # scaled to between [0,max_ticker]
    "dial-changed": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_FLOAT, )),
  }

  # Params:
  #   image_file: The filename of the image to use as the dial (will be rotated)
  #   ticker_max: The maxumum value emitted by the dial-changed signal.
  def __init__(self, image_file="dial.png", ticker_max=100):
    gtk.EventBox.__init__(self)
    self.angle = 0
    self.final_angle = 0
    self.old_angle = 0
    self.start = None
    self.ticker_max = ticker_max
    self.image_file = image_file
    # A "background" image. Never displayed, just rotated on demand. Its data is
    # extracted into a pixbuf and written to the gtk.Image that gets displayed.
    self.original = Image.open(self.image_file)
    self.center = array([x/2 for x in self.original.size])
    self.image = gtk.Image()
    self.image.set_from_file(self.image_file)
    self.add(self.image)
    self.connect("button-press-event",self.button_press_event)
    self.connect("button-release-event",self.button_release_event)
    self.connect("motion-notify-event",self.motion_notify_event)

  def show(self):
    gtk.EventBox.show(self)
    self.image.show()

  def button_press_event(self, widget, event):
    if event.button == 1:
      # Sets the vector of the position where the mouse was clicked.
      self.start = self.center - array([event.x, event.y])

  def button_release_event(self, widget, event):
    # Reset the start vector and update the angle to represent the dial's current direction
    self.start = None
    self.angle = self.angle+self.final_angle

  def motion_notify_event(self, widget, event):
    # Are we holding down the left mouse button?
    if self.start == None:
      return False
    end_rotate = self.center - array([event.x, event.y])
    # Angle between two vectors using the dot product
    self.final_angle = 180*acos(dot(self.start,end_rotate)/norm(end_rotate)/norm(self.start))/pi
    # The above formula only returns a number in the range of [0,2PI]
    # Use the sign of the cross product to convert the angle to the range [2PI,2PI]
    if cross(self.start,end_rotate) > 0:
      self.final_angle = -1*self.final_angle

    normalized = self.normalize_angle(self.angle + self.final_angle)
    old_normalized = self.old_angle*360/self.ticker_max
    if ((normalized < 225) and (old_normalized > 315)) or ((old_normalized < 225) and (normalized > 315)):
      self.start = self.center - array([event.x, event.y])
      
      return False
    
    self.rotate(self.angle + self.final_angle)

  def rotate(self, new_angle, relative = False):
    if relative:
      rotated = self.original.rotate(self.angle + new_angle)
    else:
      rotated = self.original.rotate(new_angle)
    # Convert internal Image to pixbuf, then set visible image to that pixbuf
    fd = StringIO.StringIO()
    rotated.save(fd, "ppm")
    contents = fd.getvalue()
    fd.close()
    loader = gtk.gdk.PixbufLoader("pnm")
    loader.write(contents, len(contents))
    pixbuf = loader.get_pixbuf()
    loader.close()
    self.image.set_from_pixbuf(pixbuf)
    self.emit("dial-changed", self.angle_to_ticker(new_angle))

  def normalize_angle(self, angle):
    # Image.rotate() rotates CCW when given a positive angle, which goes against
    # the convention of the cross product (aka righty-tighty, lefty-loosey),
    # so to get an angle in the range [0,360] we have to normalize it here.
    angle = -angle
    while angle < 0:
      angle = angle + 360
    while angle > 360:
      angle = angle - 360
    return angle

  def set_ticker(self, value):
    # Sets the dial to the ticker value.
    # Silently ignored if the value is outside [0,ticker_max]
    if value < 0 or value > self.ticker_max:
      return
    angle = 360-360.0*value/self.ticker_max
    self.rotate(angle)
    self.angle = angle

  def angle_to_ticker(self, angle):
    new_angle = self.normalize_angle(angle)/360*self.ticker_max
    # We round it so that the signal is only emitted max_ticker number of times
    # rather than every time the dial moves a miniscule amount.
    if round(self.old_angle) < round(new_angle):
      self.emit("dial-increase")
    if round(self.old_angle) > round(new_angle):
      self.emit("dial-decrease")
    self.old_angle = new_angle
    return self.old_angle


def destroy(widget, data=None):
  gtk.main_quit()

def fin(widget, data=None):
  print data

if __name__ == "__main__":
  window = gtk.Window(gtk.WINDOW_TOPLEVEL)
  window.connect("destroy", destroy)
  window.show()
  dial = Dial()
  dial.connect("dial-changed", fin)
  dial.show()
  window.add(dial)
  gtk.main()
