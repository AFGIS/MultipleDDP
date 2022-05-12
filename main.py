import arcpy

mxd = arcpy.mapping.MapDocument("CURRENT")
ddp = mxd.dataDrivenPages
ddpName = ddp.pageNameField.name
pageCount = 0
masterDFList = arcpy.mapping.ListDataFrames(mxd, "*bathymetry*")
masterDFList.sort(key=lambda x: x.name, reverse=False)

path = arcpy.GetParameterAsText(0)
fileName = arcpy.GetParameterAsText(1)
rangeStart = int(arcpy.GetParameterAsText(2))

#Checks for user input for the range in. Uses the end of the dataset if no range end is supplied. Also checks that
#the range input is valid
if arcpy.GetParameterAsText(3):
    rangeEnd = int(arcpy.GetParameterAsText(3)) + 1
    if rangeEnd < rangeStart:
        raise ValueError("End of range must be equal to or greater than beginning of range.")
    elif not rangeEnd < ddp.pageCount+2:
        rangeEnd = ddp.pageCount + 1
else:
    rangeEnd = ddp.pageCount + 1

# Last page requires a special case where frames are moved out of the map layout and then returned after pdf export
lastPage = False
movedFrames = []

for pageNum in range(rangeStart, rangeEnd, len(masterDFList)):
    #Update through bathymetry frames to correct DDP extent
    for index, masterDF in enumerate(masterDFList):
        # Find frame number
        masterDFName = masterDF.name.lower().replace('bathymetry', '').strip()
        # Change DDP pageNum depending on the frame so that extent, rotation, and scale from the DDP can be copied
        if pageNum + index < rangeEnd:
            ddp.currentPageID = pageNum + index
            # Set DDP rotation, scale, and extent for the second, etc frames
            masterDF.rotation = ddp.dataFrame.rotation
            masterDF.scale = ddp.dataFrame.scale
            masterDF.panToExtent(ddp.dataFrame.extent)
        else:
            # Move unused frames on the final page
            arcpy.AddMessage("Last page.")
            lastPage = True
            movedFrames.append((masterDF, masterDF.elementPositionX))
            masterDF.elementPositionX = 150

        # Search though Profiles to find matching frame number
        for profileDF in arcpy.mapping.ListDataFrames(mxd, "*profile*"):
            # Find profile frame number
            profileDFName = profileDF.name.lower().replace('profile', '').strip()
            # looks for profile number matching bathy frame number
            if masterDFName == profileDFName:
                # Move unused profile frames
                if lastPage:
                    movedFrames.append((profileDF, profileDF.elementPositionX))
                    profileDF.elementPositionX = 150
                else:
                    Name1 = ddp.pageRow.getValue(ddpName)  # need to check that there is a next row
                    # Finds the index layer "DDP" in the profile frame
                    Shp = arcpy.mapping.ListLayers(mxd, "DDP", profileDF)[0]
                    rows = arcpy.SearchCursor(Shp)
                    for row in rows:
                        # Searches DDP layer for the matching shape in DDP index layer
                        Name2 = row.getValue("DDPName")
                        extent = row.Shape.extent
                        if Name2 == Name1:
                            # When it finds a match, it pans to the extent
                            profileDF.panToExtent(extent)

    # Changes the DDP page number back to match the first Bathy frame
    ddp.currentPageID = pageNum
    arcpy.AddMessage("DDP Page ID is: " + str(ddp.currentPageID))
    # Refresh view to update extents
    arcpy.RefreshActiveView()
    # Need to track pageCount so we can only export correct pages
    pageCount += 1
    arcpy.mapping.ExportToPDF(mxd, path + "/" + fileName + str(pageCount) + ".pdf")
    arcpy.AddMessage("Exported Page# " + str(pageCount))

# reposition moved frames for convenience of later use
for frame, position in movedFrames:
    frame.elementPositionX = position
arcpy.RefreshActiveView()

del mxd, ddp, masterDFList, Shp
