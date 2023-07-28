from PyQt5.QtWidgets import QDoubleSpinBox


class NumberSpinBox(QDoubleSpinBox):
  def __init__(self, *args):
    QDoubleSpinBox.__init__(self, *args)
    self.float_min = None
    self.float_max = None

  def setFloatRange(self, fmin, fmax):
    self.setFloatMin(fmin)
    self.setFloatMax(fmax)

  def setFloatMin(self, fmin):
    self.float_min = fmin

  def setFloatMax(self, fmax):
    self.float_max = fmax

  def validate(self, value, pos):
    r = super().validate(value, pos)
    v = r[1]
    try:
      v = float(v)
      if v > self.maximum():
        self.setValue(self.maximum())
      if v < self.minimum():
        self.setValue(self.minimum())
      if self.float_max and v > self.float_max:
        v = int(v)
      elif self.float_min and v < self.float_min:
        v = int(v)
      v = f"{v}"
    except:
      pass
    return (r[0], v, r[2])
