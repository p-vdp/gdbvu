import json
from io import BytesIO
from PIL import ImageTk, Image
from tkinter import Button, Label, scrolledtext,Tk

import fiona

gdb = 'tests/S123_Photo_Log.gdb'

if __name__ == '__main__':
    lyrs = fiona.listlayers(gdb)
    img_data = dict()
    child_ids = set()
    parent_ids = set()
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
                    child_ids.add(att_id)
            # print(len(img_data), 'records')

            with fiona.open(gdb, layer=fc) as c:
                # print(c.schema)
                for i in range(1, len(c) + 1):
                    properties = c[i]['properties']
                    id = properties['globalid']
                    img_data[id]['properties'] = properties
                    parent_ids.add(id)
            # print(len(parent_ids), 'records')

    root = Tk()
    root.geometry('1000x450')

    blob = img_data['{79C2C967-F99C-4C65-AECD-663BA7D2C605}']['jpeg']
    meta = img_data['{79C2C967-F99C-4C65-AECD-663BA7D2C605}']['att_name']
    blob.seek(0)
    b = Image.open(blob)
    b = b.resize(size=(600, 400))
    # b.show()
    img = ImageTk.PhotoImage(b)

    label = Label(image=img)
    label.grid(row=1, column=0, columnspan=3)
    button_exit = Button(root, text="Exit", command=root.quit)
    button_exit.grid(row=2, column=1)
    text = Label(text=meta)
    text.grid(row=1, column=4)
    root.mainloop()
