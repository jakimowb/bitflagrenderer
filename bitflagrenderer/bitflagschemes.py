import typing
from qgis.PyQt.QtGui import QColor
from bitflagrenderer.bitflagrenderer import BitFlagScheme, BitFlagParameter, BitFlagState


def Landsat8_QA()->BitFlagScheme:
    # see https://www.usgs.gov/land-resources/nli/landsat/landsat-collection-1-level-1-quality-assessment-band?qt-science_support_page_related_con=0#qt-science_support_page_related_con
    scheme = BitFlagScheme('Landsat 8 Collection 1 QA band bits')

    p1 = BitFlagParameter('Designated Fill', 0)

    p2 = BitFlagParameter('Terrain Occlusion', 1)

    p3 = BitFlagParameter('Radiometric Saturation', 2, 2)
    p3[0].setName('No bands contain saturation')
    p3[1].setName('1-2 bands contain saturation')
    p3[1].setName('3-4 bands contain saturation')
    p3[1].setName('5 or more bands contain saturation')

    p4 = BitFlagParameter('Cloud', 4)
    p4[1].setColor('grey')

    p5 = BitFlagParameter('Cloud Confidence', 5, 2)
    p5[0].setName('Not Determined')
    p5[1].setName('Low')
    p5[2].setName('Medium')
    p5[3].setName('High')

    p6 = BitFlagParameter('Cloud Shadow Confidence', 7, 2)
    p6[0].setName('Not Determined')
    p6[1].setName('Low')
    p6[2].setName('Medium')
    p6[3].setName('High')

    p7 = BitFlagParameter('Snow/Ice Confidence', 9, 2)
    p7[0].setName('Not Determined')
    p7[1].setName('Low')
    p7[2].setName('Medium')
    p7[3].setName('High')

    p8 = BitFlagParameter('Cirrus Confidence', 11, 2)
    p8[0].setName('Not Determined')
    p8[1].setName('Low')
    p8[2].setName('Medium')
    p8[3].setName('High')

    scheme.mParameters.extend([p1, p2, p3, p4, p5, p6, p7, p8])
    return scheme


def LandsatTM_QA()->BitFlagScheme:

    scheme = Landsat8_QA()
    scheme.mName = 'Landsat 4-5 Collection 1 QA band bits'
    del scheme.mParameters[7:]
    return scheme

def LandsatMSS_QA()->BitFlagScheme:
    scheme = Landsat8_QA()
    scheme.mName = 'Landsat 1-5 MSS Collection 1 QA band bits'
    del scheme.mParameters[5:]
    return scheme


def FORCE_QAI()->BitFlagScheme:

    scheme = BitFlagScheme('FORCE Quality Assurance Information')

    p0 = BitFlagParameter('Valid data', 0)
    p0[0].setName('valid')
    p0[1].setName('no data')

    p1 = BitFlagParameter('Cloud state', 1, 2)
    p1[0].setName('clear')
    p1[1].setName('less confident cloud')
    p1[2].setName('confident, opaque cloud')
    p1[3].setName('cirrus')

    p2 = BitFlagParameter('Cloud shadow', 2, 1)

    p3 = BitFlagParameter('Snow', 3, 1)


    scheme.mParameters.extend([p0, p1, p2, p3])
    return scheme
