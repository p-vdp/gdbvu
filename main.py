import io
import json
from collections import OrderedDict
from io import BytesIO
from PIL import ImageTk, Image

import fiona
import PySimpleGUI as sg

gdb = 'tests/S123_Photo_Log.gdb'

if __name__ == '__main__':
    # read images and attributes from gdb
    lyrs = fiona.listlayers(gdb)
    img_data = dict()
    for lyr in lyrs:
        if '__ATTACH' in lyr:
            fc = lyr.split('__')[0]
            # print(fc, '->', lyr)
            with fiona.open(gdb, layer=lyr) as c:
                # print(c.schema)
                for i in range(1, len(c) + 1):
                    att_name = c[i]['properties']['ATT_NAME']
                    att_id = c[i]['properties']['REL_GLOBALID']
                    att_data = BytesIO(c[i]['properties']['DATA'])
                    img_data[att_id] = {'att_name': att_name,
                                        'jpeg': att_data}

            with fiona.open(gdb, layer=fc) as c:
                # print(c.schema)
                for i in range(1, len(c) + 1):
                    properties: OrderedDict = c[i]['properties']
                    gid = properties['globalid']
                    img_data[gid]['properties'] = properties

    gids = list(img_data.keys())
    first_image_gid = gids[0]
    current_image_index = 0
    total_count = len(gids)
    print('Loaded GlobalIDs:')
    for item in gids:
        print(item)
    print('Total records loaded: ', total_count)
    print('Starting with: ', first_image_gid)
    print('Loading GUI, do not close this window....')

    def blob_to_png(blob):
        blob.seek(0)
        img = Image.open(blob)
        img = img.resize(size=(600, 400))
        # img.show()
        bio = io.BytesIO()
        img.save(bio, format='PNG')
        del img
        return bio.getvalue()

    blob = blob_to_png(img_data[first_image_gid]['jpeg'])
    meta = img_data[first_image_gid]['att_name']
    properties = img_data[first_image_gid]['properties']

    # tabular = zip(properties.keys(), properties.values())
    # tabular_str = str()
    # for row in tabular:
    #     tabular_str += str(row[0]) + ':\t\t' + str(row[1]) + '\n'

    sg.theme('DarkAmber')
    layout = [[sg.Button('Previous'), sg.Button('Next')],
              [sg.Text(meta, key='-META-')],
              [sg.Text('1 of ' + str(total_count), key='-COUNT-')],
              [sg.Image(data=blob, key='-IMAGE-')],
              [sg.Button('Exit')]]
    window = sg.Window('gdbvu - file: ' + gdb, layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break

        if event in ['Next', 'Previous']:
            if event == 'Next' and current_image_index < (total_count - 1):
                current_image_index += 1
            elif event == 'Previous':
                current_image_index -= 1
            current_image_gid = gids[current_image_index]

            current_blob = img_data[current_image_gid]['jpeg']
            current_img = blob_to_png(current_blob)
            window['-IMAGE-'].update(data=current_img)

            current_meta = img_data[current_image_gid]['att_name']
            window['-META-'].update(current_meta)

            if current_image_index >= 0:
                current_count = current_image_index + 1
            else:
                current_count = total_count + 1 + current_image_index  # previous from first image is index -1 etc.

            # window['-COUNT-'].update('[' + str(current_image_index) + '] '+str(current_count) + ' of ' + str(total_count))
            window['-COUNT-'].update(str(current_count) + ' of ' + str(total_count))

    window.close()

    print('Exiting GUI....')
