# -*- coding: utf-8 -*-

"""
QGIS tool to convert elevation values in a raster file from GNSS ellipsoidal
heights to orthometric heights using a Geoid grid file. Note: Horizontal
coordinate system remains unchanged (input and output: EPSG:4326).

Copyright (c) 2023 Dalhousie University

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.

Additional Disclaimer:

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

__author__ = "Thomas Zuberbuehler"
__date__ = "February 2023"
__copyright__ = "(c) 2023 Dalhousie University"


import os
import io

from qgis.core import (
    QgsProcessingException,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFile,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterRasterDestination,
    QgsIconUtils,
)

from processing.algs.gdal.GdalAlgorithm import GdalAlgorithm
from processing.algs.gdal.GdalUtils import GdalUtils


class ConvertEllipsoidalToOrthometric(GdalAlgorithm):

    INPUT = "INPUT"
    GEOID_GRID_FILE = "GEOID_GRID_FILE"
    OVERWRITE = "OVERWRITE"
    OUTPUT = "OUTPUT"

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr("Input layer"),
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                self.GEOID_GRID_FILE,
                self.tr("Geoid Grid File"),
                fileFilter="Grid File (*.tif *.tiff)",
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.OVERWRITE,
                self.tr("Overwrite Existing File?"),
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr("Output Raster")
            )
        )

    def name(self):
        return "ConvertGNSSEllipsoidalHeightsToOrthometricHeights"

    def displayName(self):
        return self.tr("Convert GNSS ellipsoidal heights to orthometric heights")

    def group(self):
        return self.tr("Elevation Conversion")

    def groupId(self):
        return "elevationconversion"

    def icon(self):
        return QgsIconUtils.iconRaster()

    def commandName(self):
        return "gdalwarp"

    def getConsoleCommands(self, parameters, context, feedback, executing=True):

        source_crs = f"-s_srs \"+proj=longlat +datum=WGS84 +no_def\""

        geoid_grid_file = self.parameterAsString(parameters, self.GEOID_GRID_FILE, context)

        target_crs = f"-t_srs \"+proj=longlat +datum=WGS84 +no_defs +geoidgrids={geoid_grid_file}\""

        input_raster = self.parameterAsRasterLayer(parameters, self.INPUT, context)

        if not input_raster:
            raise QgsProcessingException(
                f"Invalid input layer {parameters[self.INPUT] if self.INPUT in parameters else 'INPUT'}")

        cell_size_x = input_raster.rasterUnitsPerPixelX()
        cell_size_y = input_raster.rasterUnitsPerPixelY()

        cell_size = f"-tr {cell_size_x} {cell_size_y}"

        output_raster = self.parameterAsOutputLayer(
            parameters, self.OUTPUT, context)

        arguments = [
            source_crs,
            target_crs,
            cell_size,
        ]

        overwrite = self.parameterAsBool(parameters, self.OVERWRITE, context)
        if overwrite:
            arguments.append("-overwrite")

        arguments.extend([
            input_raster.source(),
            output_raster,
        ])

        return [  # create command string
            self.commandName(),
            GdalUtils.escapeAndJoin(arguments)
        ]
