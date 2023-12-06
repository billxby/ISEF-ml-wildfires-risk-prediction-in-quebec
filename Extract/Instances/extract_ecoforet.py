import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import os
import matplotlib as mpl
from scipy import sparse

file_extension = "_5" # "", "_1", "_2", "_3", "_4". "_5"

coords = {
    "limits_4326": {
        "xmin":-80.4,
        "xmax": -60.6,
        "ymin": 44.6,
        "ymax": 52.6
    },
    "limits_testing_2_chunks": {
        "xmin":-70.4,
        "xmax": -70,
        "ymin": 50,
        "ymax": 50.1
    },
}
mpl.rcParams['figure.dpi'] = 120

def get_plot(gdf, target, color):
    uniques = gdf[target].unique()

    plots = []
    titles = []
    
    for item in uniques:
        if (item == "None"):
            continue

        print("Processing item ", item)
        fig, ax = plt.subplots(facecolor=(0, 0, 0, 0))
        gdf[gdf[target] == item].plot(ax=ax, color=color)
        # ax.axis('off')
        ax.set_axis_off()
        ax.set_facecolor((0, 0, 0, 0))
        # fig.savefig(str(item)+".png")
        plots.append((fig, ax))
        titles.append(item)
    
    return plots, titles

# a = sparse.csr_matrix((100, 100))
# a[0][0] = 1

# sparse.save_npz("data/ok.npz", a)

print("Start Read", flush=True)

gdf = gpd.read_file("mrnf_20k_peu_ecofo_ori_poly"+file_extension+"/mrnf_20k_peu_ecofo_ori_poly"+file_extension+".shp") # Path to the shapefile 
gdf = gdf.to_crs(4326)
gdf = gdf.fillna("None")

plots,titles = get_plot(gdf, "type_couv", "white") # The second parameter, "type" is changed depending on the Unique class's name we are extracting

target_limit = "limits_4326" 
xmin, xmax, ymin, ymax = (coords[target_limit]["xmin"]), (coords[target_limit]["xmax"]), (coords[target_limit]["ymin"]), (coords[target_limit]["ymax"])

print("Done Reading", flush=True)

min_row, max_row, min_col, max_col = 0, 575, 3, 764 
xyratio = 2/1

resx = 0.2
resy = resx/xyratio
n_chunkx = int(round((xmax-xmin)/resx, 1)) # MAKE SURE YOU CAN MATH: because we convert to int if you get 0.1232131 sketch 
n_chunky = int(round((ymax-ymin)/resy, 1)) # We're using round to not get like 2.9999999999999999997 make sure to get 0.3

for item_idx in range(len(plots)):
    # Declare sparse matrix with a defined width, so we can concat later on axis = 0
    

    smat_item = sparse.csr_matrix(((max_row-min_row+1)*n_chunky, 0)) 

    plots[item_idx][0].tight_layout(pad=0, rect=(0,0,0,0))

    for x_idx in range(n_chunkx):
        # Similarly, declare a sparse matrix with a defined height for easier concat on axis = 1
        smat_chunk_row = sparse.csr_matrix((0, max_col-min_col+1))

        print(round(xmin+(x_idx)*resx, 1),
                round(xmin+(x_idx+1)*resx, 1))

        for y_idx in range(n_chunky):
            plots[item_idx][1].axis([
                round(xmin+(x_idx)*resx, 1),
                round(xmin+(x_idx+1)*resx, 1), # We don't want to get .00000000000000000000001 it's gonna ruin the perfect allignment,
                round(ymin+(y_idx)*resy, 1),
                round(ymin+(y_idx+1)*resy, 1)
            ])

            # print(round(xmin+(x_idx)*resx, 1),
            #     round(xmin+(x_idx+1)*resx, 1),
            #     round(ymin+(y_idx)*resy, 1),
            #     round(ymin+(y_idx+1)*resy, 1))
            
            plots[item_idx][0].canvas.draw()
            data = np.frombuffer(plots[item_idx][0].canvas.buffer_rgba(), dtype=np.uint8)
            image = data.reshape(plots[item_idx][0].canvas.get_width_height()[::-1] + (4,)) # Get the 3d array of the chunk
            new_image = np.round(np.squeeze(image[:, :, 3:])/255.0, 3)[:, min_col:max_col+1] # Convert to matrix & get relevant area only

            # print(new_image.shape)

            smat_chunk_row = sparse.vstack((sparse.csr_matrix(new_image), smat_chunk_row))
            del data, image, new_image # Save memory 
        
        # print(smat_chunk_row.shape, smat_item.shape)

        smat_item = sparse.hstack((smat_item, smat_chunk_row))
        del smat_chunk_row

    print("Finished processing this ", titles[item_idx])
    sparse.save_npz("data/"+titles[item_idx]+".npz", smat_item) # Save the sparse matrix
    del smat_item # Free Up Memory

# print("WHAT IS GOING ON")

os.system("sudo poweroff")