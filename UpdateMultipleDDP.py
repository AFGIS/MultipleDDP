import arcpy

mxd = arcpy.mapping.MapDocument("CURRENT")
ddp = mxd.dataDrivenPages
ddpName = ddp.pageNameField.name
masterDFList = arcpy.mapping.ListDataFrames(mxd, "*bathymetry*")
masterDFList.sort(key=lambda x: x.name, reverse=False)

rangeStart = ddp.currentPageID
rangeEnd = ddp.currentPageID+1

# Last page requires a special case where frames are moved out of the map layout and then returned after pdf export
lastPage = False

for pageNum in range(rangeStart, rangeEnd):
    #Update through bathymetry frames to correct DDP extent
    for index, masterDF in enumerate(masterDFList):
        # Find frame number
        masterDFName = masterDF.name.lower().replace('bathymetry', '').strip()
        # Change DDP pageNum depending on the frame so that extent, rotation, and scale from the DDP can be copied
        if pageNum + index < ddp.pageCount+1:
            ddp.currentPageID = pageNum + index
            # Set DDP rotation, scale, and extent for the second, etc frames
            masterDF.rotation = ddp.dataFrame.rotation
            masterDF.scale = ddp.dataFrame.scale
            masterDF.panToExtent(ddp.dataFrame.extent)
        else:
            # If the previous frame was the last DDP frame, turn off unused layers
            lastPage = True
            for lyr in arcpy.mapping.ListLayers(mxd, "", masterDF):
                lyr.visible = False

        # Search though Profiles to find matching frame number
        subFrameListofLists = [arcpy.mapping.ListDataFrames(mxd, "*profile*"), arcpy.mapping.ListDataFrames(mxd, "*bar*")]
        for subFrameList in subFrameListofLists:
            for profileDF in subFrameList:
                # Find profile frame number
                profileDFName = profileDF.name.lower()
                if "profile" in profileDFName:
                    profileDFName = profileDFName.replace('profile', '').strip()
                elif "bar" in profileDFName:
                    profileDFName = profileDFName.replace('bar', '').strip()
                # looks for profile number matching bathy frame number
                if masterDFName == profileDFName:
                    # If the previous frame was the last DDP frame, turn off unused layers
                    if lastPage:
                        for lyr in arcpy.mapping.ListLayers(mxd, "*", profileDF):
                            lyr.visible = False
                    else:
                        Name1 = ddp.pageRow.getValue(ddpName)  # need to check that there is a next row
                        # Finds the index layer "DDP" in the profile frame
                        if len(arcpy.mapping.ListLayers(mxd, "*DDP*", profileDF)) == 0:
                            arcpy.AddMessage("Error: DDP layer is missing from Profile. ")
                            exit(1)
                        else:
                            Shp = arcpy.mapping.ListLayers(mxd, "*DDP*", profileDF)[0]
                            arcpy.SelectLayerByAttribute_management(Shp, "CLEAR_SELECTION")
                            rows = arcpy.SearchCursor(Shp)
                            for row in rows:
                                # Searches DDP layer for the matching shape in DDP index layer
                                Name2 = row.getValue("DDPName")
                                extent = row.Shape.extent
                                if float(Name2) == float(Name1):
                                    # When it finds a match, it pans to the extent
                                    profileDF.panToExtent(extent)
                                    break
                            del Shp

    # Changes the DDP page number back to match the first Bathy frame
    ddp.currentPageID = pageNum
    arcpy.AddMessage("DDP Page ID is: " + str(ddp.currentPageID))
    # Refresh view to update extents
    arcpy.RefreshActiveView()

del mxd, ddp, masterDFList


