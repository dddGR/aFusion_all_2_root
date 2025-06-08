"""This file acts as the main module for this script."""

import traceback, adsk.core, adsk.fusion
# import adsk.cam

import re, json
# from .BodiesGroupFactry import bodiesGroupFactry

# more info on fusion API: https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-7B5A90C8-E94C-48DA-B16B-430729B734DC

app = adsk.core.Application.get()
ui  = app.userInterface


def getSurfaceGroupsID() -> int:

    _app = adsk.core.Application.get()

    for i in range(10, 21):
        Properties = _app.executeTextCommand(u'PEntity.Properties {}'.format(i))
        jsonProp = json.loads(Properties)

        if jsonProp.get("interfaceId") == "Ns::BREP::SurfaceGroups":
            return i
    
    return -1


# Create Group from set of bodies
# the code is from here: https://forums.autodesk.com/t5/fusion-api-and-scripts-forum/feature-request-api-for-creating-and-managing-quot-group-quot-s/m-p/9905701/highlight/true#M10023
def createGroup(groupName :str, bodiesList :list, id :int):

    _app = adsk.core.Application.get()
    _ui = _app.userInterface
    des  :adsk.fusion.Design = app.activeProduct
    root :adsk.fusion.Component = des.rootComponent

    # selections
    sels :adsk.core.Selections = _ui.activeSelections
    sels.clear()

    # select root bodies
    bodies :adsk.fusion.BRepBodies = root.bRepBodies
    sels.add(bodies)

    # Create SurfaceGroup
    _app.executeTextCommand(u'Commands.Start FusionCreateSurfaceGroupCommand')

    # get SurfaceGroups Properties
    # SurfaceGroups(SurfaceGroupsMetaType id: 21)  
    surfaceGroupsProp = _app.executeTextCommand(u'PEntity.Properties {}'.format(id)) # Id change after v.2602.1.14 – May 27, 2025 update
    
    # Convert to json
    surfaceGroups = json.loads(surfaceGroupsProp)

    surfaceGroups_count = len(surfaceGroups['children'])

    targetId = surfaceGroups['children'][surfaceGroups_count - 1]['entityId']

    if len(groupName) > 0: # Rename SurfaceGroup
        _app.executeTextCommand(u'PInterfaces.Rename {} {}'.format(targetId, groupName))

    # select bodiesList
    [sels.add(body) for body in bodiesList]

    # select SurfaceGroup
    # https://github.com/kantoku-code/Fusion360_Small_Tools_for_Developers/blob/master/TextCommands/TextCommands_txt_Ver2_0_8176.txt#L2058
    # Except for the root component, the <Paths> need to be changed.
    # _app.executeTextCommand(u'Selections.Add 57:3:21:{}'.format(targetId))

    # exec FusionMoveToSurfaceGroupCommand
    _app.executeTextCommand(u'Commands.Start FusionMoveToSurfaceGroupCommand')
    _app.executeTextCommand(u'NuCommands.CommitCmd')



def run(_context: str):
    """This function is called by Fusion when the script is run."""
    
    try:
        design: adsk.fusion.Design = app.activeProduct
        if not design:
            ui.messageBox('No active design found.')
            return

        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        rootComp: adsk.fusion.Component = design.rootComponent
        
        # unested components first, to prevent after copy to root component, new name
        # and group will be split to multiple groups because of nested components
        for occurrence in list(rootComp.occurrences):
            if occurrence.component.occurrences.count == 0:
                # this component has no nested components
                continue
            
            # get all bodies in all nested components and copy to main component
            for sub_occ in occurrence.component.allOccurrences:
                for body in sub_occ.bRepBodies:
                    body.copyToComponent(occurrence)

                    # deleted old body (no need, main component will be
                    # remove after script is done), keep to use later, maybe
                    # sub_occ.component.features.removeFeatures.add(body)

        
        # occs = list(rootComp.allOccurrences)  # get all the occurrences (all mean all, including nested one)
                                                # not use anymore after add unested component block above
                                                # still keep to use later, maybe..

        occs = list(rootComp.occurrences) # get the list of all occurrences in root level

        body_groups: dict = {}
        comp_index: dict = {}

        # Copy all bodies to root component, and rename them
        # New bodies will be sorted and grouped, body and group will be named after originated
        # component name (with suffix if have multiple bodies inside one component).
        # Number of groups will be the same as number of originalcomponents (at the root level)
        for occ in occs:
            body_index: int = 1

            group_name = re.sub(r'\s*\(\d+\)\s*', '', occ.name).strip().split(':')[0]

            if group_name not in body_groups:
                body_groups[group_name] = []
                comp_index[group_name] = 1
            else:
                comp_index[group_name] += 1

            # Note: bRepBodies is call at the occurrence level instead of
            # component to preserve current position of body in design.
            for body in occ.bRepBodies: 
                newBody = body.copyToComponent(rootComp)
                newBody.name = f"{group_name}-{comp_index[group_name]}.{body_index}"
                body_index += 1

                body_groups[group_name].append(newBody)
        
        # Sort bodies by name and create groups by name
        body_groups_sorted = dict(sorted(body_groups.items()))

        sf_id: int = getSurfaceGroupsID()

        if sf_id == -1:
            ui.messageBox('[WARNING] SurfaceGroups ID not found. Body not grouped.')
            return

        # groupFact = bodiesGroupFactry()
        for group_name, body_list in body_groups_sorted.items():
            # groupFact.createBodiesGroup(body_list, group_name)
            if len(body_list) > 1:
                createGroup(group_name, body_list, sf_id)
        
        # Remove old components (not delete to revert if needed)
        for occ in occs:
            rootComp.features.removeFeatures.add(occ)

        ui.messageBox('All bodies have been moved to root and sorted.')
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
