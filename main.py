import io
import os
import json
from collections import OrderedDict
from io import BytesIO
from PIL import ImageTk, Image

import fiona
import PySimpleGUI as sg


def blob_to_png(b):
    b.seek(0)
    img = Image.open(b)
    img = img.resize(size=(600, 400))
    # img.show()
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    del img
    return bio.getvalue()


def blob_to_file(b, out_jpeg):
    b.seek(0)
    img = Image.open(b)
    img.save(out_jpeg, format='JPEG')
    del img
    # print('Saved ', out_jpeg)


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
    # print('Loaded GlobalIDs:')
    # for item in gids:
    #     print(item)
    # print('Total records loaded: ', total_count)
    # print('Starting with: ', first_image_gid)
    print('Loading GUI, do not close this window....')

    blob = blob_to_png(img_data[first_image_gid]['jpeg'])  # TODO put this block into functions
    meta = img_data[first_image_gid]['att_name']
    properties = img_data[first_image_gid]['properties']
    attrs: list = list(zip(properties.keys(), properties.values()))
    # print(list(attrs))

    sg.theme('DarkAmber')

    layout = [[sg.Text('Export folder:'), sg.In(size=(50, 1), enable_events=True, key='-FOLDER-'), sg.FolderBrowse(),
               sg.Button('Export all', key='-EXPORT-', disabled=True)],
              [sg.Image(data=blob, key='-IMAGE-')],
              [sg.Button('Previous'), sg.Button('Next'), sg.Text(meta, key='-META-'), sg.Text('1 of ' + str(total_count), key='-COUNT-')],
              [sg.Table(values=attrs, key='-ATTRIBUTES-', headings=['Field', 'Attribute'],
                        justification='left', auto_size_columns=False, col_widths=[15, 50])]]

    window = sg.Window('gdbvu - file: ' + gdb, layout, return_keyboard_events=True, use_default_focus=False)

    while True:
        event, values = window.read()
        # print(event)
        # print(values)

        if event == sg.WIN_CLOSED or event in ['Exit', 'Escape:27']:
            break

        if event in ['Next', 'Right:39', 'Previous', 'Left:37']:
            if event in ['Next', 'Right:39'] and current_image_index < (total_count - 1):
                current_image_index += 1
            elif event in ['Previous', 'Left:37']:
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

            properties = img_data[current_image_gid]['properties']
            attrs: list = list(zip(properties.keys(), properties.values()))
            window['-ATTRIBUTES-'].update(attrs)

        if event == '-FOLDER-':
            export_folder = values['-FOLDER-']
            # print(export_folder)
            window['-EXPORT-'].update(disabled=False)

        if event == '-EXPORT-':
            # print(export_folder)
            if not os.path.exists(export_folder):
                sg.popup_annoying('ERROR: Folder path does not exist\n\n' + export_folder)
            else:
                for i, gid in enumerate(gids):
                    sg.one_line_progress_meter(title='Export', current_value=i+1, max_value=len(gids), no_button=True, orientation='h')
                    filename = img_data[gid]['att_name']
                    file_blob = img_data[gid]['jpeg']
                    out_file = os.path.join(export_folder, filename)
                    blob_to_file(file_blob, out_file)

                sg.popup('Exported ' + str(total_count) + ' files to:\n' + export_folder)

    window.close()

    print('Exiting GUI....')
