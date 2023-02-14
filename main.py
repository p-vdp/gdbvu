import io
import os
import pandas as pd
from io import BytesIO
from PIL import Image
from sys import argv

import fiona
import PySimpleGUI as sg  # noqa


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


def open_gdb(gdb=None, lyr=None):
    if not gdb or not lyr:
        gdb = sg.Window('gdbvu',
                        [[sg.Text('Select a .gdb folder')],
                         [sg.In(), sg.FolderBrowse()],
                         [sg.Open(), sg.Cancel()]]).read(close=True)[1][0]
        lyrs = fiona.listlayers(gdb)
        ev, val = sg.Window('Select an ATTACH layer',
                            layout=[[sg.Listbox(lyrs, key='-LIST-',
                                                size=(max([len(str(v)) for v in lyrs]) + 2, len(lyrs)),
                                                select_mode='extended', bind_return_key=True), sg.OK()]]).read(
            close=True)

        lyr = val['-LIST-'][0]

    fc = lyr.split('__')[0]

    if '__ATTACH' not in lyr:
        sg.popup_error('Selected layer is not an attachments table')
        exit(1)

    data = dict()
    with fiona.open(gdb, layer=lyr) as c:
        # print(c.schema)
        try:
            for item in range(1, len(c) + 1):
                att_name = c[item]['properties']['ATT_NAME']
                att_id = c[item]['properties']['REL_GLOBALID']
                att_data = BytesIO(c[item]['properties']['DATA'])
                data[att_id] = {'jpeg': att_data,
                                'properties': {
                                    'att_name': att_name}
                                }
        except TypeError:
            sg.popup_error('Attachments table not found')

    with fiona.open(gdb, layer=fc) as c:
        # print(c.schema)
        try:
            for item in range(1, len(c) + 1):
                prop = dict(c[item]['properties'])
                gd = prop['globalid']
                for ky in prop:
                    data[gd]['properties'][ky] = prop[ky]
        except TypeError:
            sg.popup_error('No attachments found')

    return data, lyr


if __name__ == '__main__':
    if len(argv) > 1:  # load from parameters
        img_data, lyr_name = open_gdb(argv[1], argv[2])
    else:  # load gdb from file
        img_data, lyr_name = open_gdb()

    gids = list(img_data.keys())
    first_image_gid = gids[0]
    current_image_index = 0
    total_count = len(gids)

    blob = blob_to_png(img_data[first_image_gid]['jpeg'])
    meta = img_data[first_image_gid]['properties']['att_name']
    properties = img_data[first_image_gid]['properties']
    attrs: list = list(zip(properties.keys(), properties.values()))

    # gui stuff
    print('Loading GUI, do not close this window....')
    # sg.theme('DarkAmber')

    widget_export = [sg.Text('Export folder:'), sg.In(size=(50, 1), enable_events=True, key='-FOLDER-'),
                     sg.FolderBrowse(),
                     sg.Button('Export all', key='-EXPORT-', disabled=True)]
    widget_main_image = sg.Image(data=blob, key='-IMAGE-')
    widget_prev = sg.Button('Previous')
    widget_next = sg.Button('Next')
    widget_filename = sg.Text(meta, key='-META-')
    widget_count = sg.Text('1 of ' + str(total_count), key='-COUNT-')
    widget_tbl = [sg.Table(values=attrs, key='-ATTRIBUTES-', headings=['Field', 'Attribute'],
                           justification='left', auto_size_columns=True, vertical_scroll_only=False,
                           size=(35, 26), expand_x=True, expand_y=True)]

    left_layout = [  # sg.Image(enable_events=True, key=unique img id
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')],
        [sg.Text('placeholder for scrolling pane')]
    ]

    center_layout = [
        [widget_prev, widget_next, widget_filename, widget_count],
        [widget_main_image],
        widget_export
    ]

    right_layout = [
        widget_tbl
    ]

    full_layout = [[sg.Column(left_layout, scrollable=True, expand_y=True), sg.Column(center_layout), sg.Column(right_layout)]]
    window = sg.Window('gdbvu', full_layout, return_keyboard_events=True, use_default_focus=False, resizable=True)

    while True:
        event, values = window.read()
        print(event)
        print(values)

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

            current_meta = img_data[current_image_gid]['properties']['att_name']
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
            # print(export_folder)
            window['-EXPORT-'].update(disabled=False)

        if event == '-EXPORT-':
            export_folder = values['-FOLDER-']
            # print(export_folder)
            if not os.path.exists(export_folder):
                sg.popup_annoying('ERROR: Folder path does not exist\n\n' + export_folder)
            else:
                out_tbl = list()
                for k in img_data:
                    out_tbl.append(img_data[k]['properties'])
                out_tbl = pd.json_normalize(out_tbl)
                out_xlsx = os.path.join(export_folder, lyr_name + '.xlsx')
                out_tbl.to_excel(out_xlsx)

                for i, gid in enumerate(gids):
                    sg.one_line_progress_meter(title='Export', current_value=i + 1, max_value=len(gids), no_button=True, orientation='h')
                    filename = img_data[gid]['properties']['att_name']
                    file_blob = img_data[gid]['jpeg']
                    out_file = os.path.join(export_folder, filename)
                    blob_to_file(file_blob, out_file)

                sg.popup(f'Exported {str(total_count)} files to:\n'
                         f'{export_folder}\n\n'
                         f'Exported metadata table to:\n'
                         f'{out_xlsx}')

            # if event.startswith('IMAGE_No_'):
            #   process sidebar image, make it main

    window.close()

    print('Exiting GUI....')
