"""This file acts as the main module for this script."""

import traceback, adsk.core, adsk.fusion
# import adsk.cam

import re
from .BodiesGroupFactry import bodiesGroupFactry

# more info on fusion API: https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-7B5A90C8-E94C-48DA-B16B-430729B734DC

def run(_context: str):
    """This function is called by Fusion when the script is run."""
    
    app = adsk.core.Application.get()
    ui  = app.userInterface

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

        groupFact = bodiesGroupFactry()
        for group_name, body_list in body_groups_sorted.items():
            groupFact.createBodiesGroup(body_list, group_name)

        # Remove old components (not delete to revert if needed)
        for occ in occs:
            rootComp.features.removeFeatures.add(occ)

        ui.messageBox('All bodies have been moved to root and sorted.')
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
