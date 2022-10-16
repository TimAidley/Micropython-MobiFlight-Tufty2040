from picographics import PicoGraphics, DISPLAY_TUFTY_2040
from math import cos, sin, radians



class AttitudeIndicator:
    def __init__(self, display):
        self.display = display
        self.pitchScale = 2
        self.pitchLimit = 60
        self.bankLimit = 100
        self.ground = display.create_pen(185, 119, 4)
        self.sky = display.create_pen(52, 152, 219)
        self.white = display.create_pen(255, 255, 255)
        self.black = display.create_pen(0, 0, 0)
        self.cx = 160
        self.cy = 120
        self.innerRadius = 80
        self.outerRadius = 110
        self.innerHeight = self.pitchLimit * 3;
        self.fives = 10
        self.tens = 20
        
    def transformPt(self, x, y, bank, pitch):
        rad = radians(bank)
        cosrad = cos(rad)
        sinrad = sin(rad)
        yy = (y + pitch) * self.pitchScale
        return (int(self.cx + x * cosrad - yy * sinrad), int(self.cy + x * sinrad + yy * cosrad))
    
    def drawInner(self, bank, pitch):
        tl = self.transformPt(-self.innerRadius, -self.innerHeight, bank, pitch)
        tr = self.transformPt(self.innerRadius, -self.innerHeight, bank, pitch)
        l = self.transformPt(-self.innerRadius, 0, bank, pitch)
        r = self.transformPt(self.innerRadius, 0, bank, pitch)
        bl = self.transformPt(-self.innerRadius, self.innerHeight, bank, pitch)
        br = self.transformPt(self.innerRadius, self.innerHeight, bank, pitch)
        
        self.display.set_pen(self.sky)
        self.display.polygon([l, tl, tr, r])
        self.display.set_pen(self.ground)
        self.display.polygon([l, r, br, bl])
        
        # Lines
        self.display.set_pen(self.white)
        self.display.line(l[0], l[1], r[0], r[1])
        
        for y in range(-20, 30, 10):
            l = self.transformPt(-self.tens, y, bank, pitch)
            r = self.transformPt(self.tens, y, bank, pitch)
            self.display.line(l[0], l[1], r[0], r[1])
            
        for y in range(-15, 25, 10):
            l = self.transformPt(-self.fives, y, bank, pitch)
            r = self.transformPt(self.fives, y, bank, pitch)
            self.display.line(l[0], l[1], r[0], r[1])
            
    def outerPts(self, angle, d1, d2, d3):
        rada = radians(-angle)
        x = cos(rada)
        y = sin(rada)
        return ((int(self.cx + d1 * x), int(self.cy + d1 * y)),
                (int(self.cx + d2 * x), int(self.cy + d2 * y)),
                (int(self.cx + d3 * x), int(self.cy + d3 * y)))
            
    def drawOuter(self, bank, pitch):
        pts = list(map(lambda x : self.outerPts(x - bank, self.innerRadius, self.outerRadius, 200), range(0, 360, 10)))
        #print(pts)
        for a in range(len(pts)):
            b = (a + 1) % len(pts)
            if a < len(pts) / 2:
                self.display.set_pen(self.sky)
            else:
                self.display.set_pen(self.ground)
            
            self.display.polygon(pts[a][0], pts[a][1], pts[b][1], pts[b][0])
            self.display.set_pen(self.black)
            self.display.polygon(pts[a][1], pts[a][2], pts[b][2], pts[b][1])
            self.display.line(pts[a][0][0], pts[a][0][1], pts[b][0][0], pts[b][0][1])
            
    def draw(self, bank, pitch):   
        self.drawInner(bank, pitch)
        self.drawOuter(bank, pitch)

if False:
    display = PicoGraphics(display=DISPLAY_TUFTY_2040)
    black = display.create_pen(0,0,0)
    display.clear()
    
    ai = AttitudeIndicator(display)
    ai.drawInner(10, 20)
    ai.drawOuter(10, 20)
    
    display.update()