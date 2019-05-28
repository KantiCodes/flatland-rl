import time

# from matplotlib import pyplot as plt
import numpy as np
from PyQt5 import QtSvg
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout
from numpy import array

from flatland.envs.agent_utils import EnvAgent
from flatland.utils.graphics_layer import GraphicsLayer
from flatland.utils.graphics_qt import QtRenderer
from flatland.utils.svg import Track, Zug


def transform_string_svg(sSVG):
    sSVG = sSVG.replace("ASCII", "UTF-8")
    bySVG = bytearray(sSVG, encoding='utf-8')
    return bySVG


def create_QtSvgWidget_from_svg_string(sSVG):
    svgWidget = QtSvg.QSvgWidget()
    ret = svgWidget.renderer().load(transform_string_svg(sSVG))
    if ret is False:
        print("create_QtSvgWidget_from_svg_string : failed to parse:", sSVG)
    return svgWidget


class QTGL(GraphicsLayer):
    def __init__(self, width, height):
        self.cell_pixels = 60
        self.tile_size = self.cell_pixels

        self.width = width
        self.height = height

        # Total grid size at native scale
        self.widthPx = self.width * self.cell_pixels
        self.heightPx = self.height * self.cell_pixels
        self.qtr = QtRenderer(self.widthPx, self.heightPx, ownWindow=True)

        self.qtr.beginFrame()
        self.qtr.push()

        # This comment comes from minigrid.  Not sure if it's still true. Jeremy.
        # Internally, we draw at the "large" full-grid resolution, but we
        # use the renderer to scale back to the desired size
        self.qtr.scale(self.tile_size / self.cell_pixels, self.tile_size / self.cell_pixels)

        self.tColBg = (255, 255, 255)  # white background
        # self.tColBg = (220, 120, 40)    # background color
        self.tColRail = (0, 0, 0)  # black rails
        self.tColGrid = (230,) * 3  # light grey for grid

        # Draw the background of the in-world cells
        self.qtr.fillRect(0, 0, self.widthPx, self.heightPx, *self.tColBg)
        self.qtr.pop()
        self.qtr.endFrame()

    def plot(self, gX, gY, color=None, lw=2, **kwargs):
        color = self.adaptColor(color)

        self.qtr.setLineColor(*color)
        lastx = lasty = None

        if False:
            for x, y in zip(gX, gY):
                if lastx is not None:
                    # print("line", lastx, lasty, x, y)
                    self.qtr.drawLine(
                        lastx * self.cell_pixels, -lasty * self.cell_pixels,
                        x * self.cell_pixels, -y * self.cell_pixels)
                lastx = x
                lasty = y
        else:
            gPoints = np.stack([array(gX), -array(gY)]).T * self.cell_pixels
            self.qtr.setLineWidth(5)
            self.qtr.drawPolyline(gPoints)

    def scatter(self, gX, gY, color=None, marker="o", s=50, *args, **kwargs):
        color = self.adaptColor(color)
        self.qtr.setColor(*color)
        self.qtr.setLineColor(*color)
        r = np.sqrt(s)
        gPoints = np.stack([np.atleast_1d(gX), -np.atleast_1d(gY)]).T * self.cell_pixels
        for x, y in gPoints:
            self.qtr.drawCircle(x, y, r)

    def text(self, x, y, sText):
        self.qtr.drawText(x * self.cell_pixels, -y * self.cell_pixels, sText)

    def prettify(self, *args, **kwargs):
        pass

    def prettify2(self, width, height, cell_size):
        pass

    def show(self, block=False):
        pass

    def pause(self, seconds=0.00001):
        pass

    def beginFrame(self):
        self.qtr.beginFrame()
        self.qtr.push()
        self.qtr.fillRect(0, 0, self.widthPx, self.heightPx, *self.tColBg)

    def endFrame(self):
        self.qtr.pop()
        self.qtr.endFrame()


class QTSVG(GraphicsLayer):
    def __init__(self, width, height):
        self.app = QApplication([])
        self.wWinMain = QMainWindow()

        self.wMain = QWidget(self.wWinMain)

        self.wWinMain.setCentralWidget(self.wMain)

        self.layout = QGridLayout()
        self.layout.setSpacing(0)
        self.wMain.setLayout(self.layout)
        self.wWinMain.resize(600, 600)
        self.wWinMain.show()
        self.wWinMain.setFocus()

        self.track = self.track = Track()
        self.lwTrack = []
        self.zug = Zug()

        self.lwAgents = []
        self.agents_prev = []

        # svgWidget = None

    def is_raster(self):
        return False

    def processEvents(self):
        self.app.processEvents()
        time.sleep(0.001)

    def clear_rails(self):
        # print("Clear rails: ", len(self.lwTrack))
        for wRail in self.lwTrack:
            self.layout.removeWidget(wRail)
        self.lwTrack = []
        self.clear_agents()

    def clear_agents(self):
        # print("Clear Agents: ", len(self.lwAgents))
        for wAgent in self.lwAgents:
            self.layout.removeWidget(wAgent)
        self.lwAgents = []
        self.agents_prev = []

    def setRailAt(self, row, col, binTrans, target=None):
        if binTrans in self.track.dSvg:
            sSVG = self.track.dSvg[binTrans].to_string()
            svgWidget = create_QtSvgWidget_from_svg_string(sSVG)
            self.layout.addWidget(svgWidget, row, col)
            self.lwTrack.append(svgWidget)
        else:
            print("Illegal rail:", row, col, format(binTrans, "#018b")[2:])

    def setAgentAt(self, iAgent, row, col, iDirIn, iDirOut, color=None):
        if iAgent < len(self.lwAgents):
            wAgent = self.lwAgents[iAgent]
            agentPrev = self.agents_prev[iAgent]

            # If we have an existing agent widget, we can just move it
            if wAgent is not None:
                self.layout.removeWidget(wAgent)
                self.layout.addWidget(wAgent, row, col)

                # We can only reuse the image if noth new and old are straight and the same:
                if iDirIn == iDirOut and \
                   agentPrev.direction == iDirIn and \
                   agentPrev.old_direction == agentPrev.direction:
                    return
                else:
                    # need to load new image
                    # print("new dir:", iAgent, row, col, agentPrev.direction, iDirIn)
                    agentPrev.direction = iDirOut
                    agentPrev.old_direction = iDirIn
                    sSVG = self.zug.getSvg(iAgent, iDirIn, iDirOut, color=color).to_string()
                    wAgent.renderer().load(transform_string_svg(sSVG))
                    return

        # Ensure we have adequate slots in the list lwAgents
        for i in range(len(self.lwAgents), iAgent + 1):
            self.lwAgents.append(None)
            self.agents_prev.append(None)

        # Create a new widget for the agent
        sSVG = self.zug.getSvg(iAgent, iDirIn, iDirOut, color=color).to_string()
        svgWidget = create_QtSvgWidget_from_svg_string(sSVG)
        self.lwAgents[iAgent] = svgWidget
        self.agents_prev[iAgent] = EnvAgent((row, col), iDirOut, (0, 0), old_direction=iDirIn)
        self.layout.addWidget(svgWidget, row, col)

    def show(self, block=False):
        self.wMain.update()

    def resize(self, env):
        screen_resolution = self.app.desktop().screenGeometry()
        width, height = screen_resolution.width(), screen_resolution.height()
        w = np.ceil(width * 0.8 / env.width)
        h = np.ceil(height * 0.8 / env.height)
        self.wWinMain.resize(env.width * w, env.height * h)
        self.wWinMain.move((width - env.width * w) / 2, (height - env.height * h) / 2)


def main2():
    gl = QTGL(10, 10)
    for i in range(10):
        gl.beginFrame()
        gl.plot([3 + i, 4], [-4 - i, -5], color="r")
        gl.endFrame()
        time.sleep(1)


def main():
    gl = QTSVG()

    for i in range(1000):
        gl.processEvents()
        time.sleep(0.1)
    time.sleep(1)


if __name__ == "__main__":
    main()
