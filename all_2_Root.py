"""This file acts as the main module for this script."""

import traceback, adsk.core, adsk.fusion
# import adsk.cam

import re
from .BodiesGroupFactry import bodiesGroupFactry

# Initialize the global variables for the Application and UserInterface objects.
app = adsk.core.Application.get()
ui  = app.userInterface

def run(_context: str):
    """This function is called by Fusion when the script is run."""

    try: 
        design: adsk.fusion.Design = app.activeProduct
        if not design:
            ui.messageBox('No active design found.')
            return
        
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        rootComp: adsk.fusion.Component = design.rootComponent

        occs = list(rootComp.allOccurrences)

        body_groups: dict = {}
        comp_index: dict = {}

        # Copy bodies to root and sort them
        for occ in occs:
            body_index: int = 1

            group_name = re.sub(r'\s*\(\d+\)\s*', '', occ.name).strip().split(':')[0]

            if group_name not in body_groups:
                body_groups[group_name] = []
                comp_index[group_name] = 1
            else:
                comp_index[group_name] += 1

            for body in occ.bRepBodies:
                newBody = body.copyToComponent(rootComp)
                newBody.name = f"{group_name}-{comp_index[group_name]}.{body_index}"
                body_index += 1

                body_groups[group_name].append(newBody)

        # for occ in occs:
        #     bodyIndex: int = 1
        #     for body in occ.bRepBodies:
        #         newBody = body.copyToComponent(rootComp)

        #         prefix = re.sub(r'\s*\(\d+\)\s*', '', occ.name).strip()
        #         newBody.name = f"{prefix}-{bodyIndex}"
        #         bodyIndex += 1

        #         group_name = prefix.split(':')[0]

        #         if group_name not in body_groups:
        #             body_groups[group_name] = []
        #         body_groups[group_name].append(newBody)
        
        # Sort bodies by name
        body_groups_sorted = dict(sorted(body_groups.items()))

        groupFact = bodiesGroupFactry()
        for group_name, body_list in body_groups_sorted.items():
            groupFact.createBodiesGroup(body_list, group_name)

        # Delete old components
        for occ in occs:
            rootComp.features.removeFeatures.add(occ)

        ui.messageBox('All bodies have been moved to root and sorted.')
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
