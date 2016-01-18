'''
Fracture Rig!
Author: Steven Burrichter
Company: Side Effects Software
Last Updated: 10/1/2015
Reference Build: H15.0.252

IMPORTANT NOTES
1) Make sure the object you want to fracture is at the origin and has NO
transform modifications. Feel free to put an xform node at the SOP level, but
be warned that if you get any weird rotations or jittering, transforms are the
first culprit.

2) Set up your simulation exactly how you want it. If the transforms are set
properly, the pieces will be 1:1 with the simulation. THEN press the button.
This tool is designed to be the very last step in the process.
'''

import hou

class FRACTURE_RIG:
    ######################################
    #VARIABLES
    ######################################
    numberOfPieces  =   []
    nodeGeo         =   None
    nodeSubnet      =   None
    nodePieces      =   []
    nodeDisplay     =   []
    PARMS           =   ["tx", "ty", "tz", "rx", "ry", "rz", "px", "py", "pz"]

    ######################################
    #FUNCTIONS
    ######################################

    #################################
    #Did the user actually grab the
    #correct node?
    #################################
    def CheckObject(self):
        self.nodeGeo = hou.selectedNodes()

        if len(self.nodeGeo) > 1:
            #Multiple assets
            #TODO: Check all nodes are the same before moving forward
            node_type = self.nodeGeo[0].type()
        elif len(self.nodeGeo) < 1:
            return False
        else:
            node_type = self.nodeGeo[0].type()

        #TODO: Solve for multiple nodes
        if self.nodeGeo[0].parm('soppath') == None:
            print "DOP Node doesn't contain a soppath!"
            return False
        else:
            return True

    #################################
    #Grabs the initial data
    #################################
    def GrabPieces(self):
        self.nodeDisplay = self.FindReferenceGeometry()

        for index in range(0, len(self.nodeDisplay)):
            obj_geometry = self.nodeDisplay[index].geometry()

            if obj_geometry.findPointAttrib("name") == None:
                list_pieces = obj_geometry.findPrimAttrib("name").strings()
            else:
                list_pieces = obj_geometry.findPointAttrib("name").strings()

            self.numberOfPieces.append(len(list_pieces))

    #################################
    #Creates the subnet to contain
    #the animated pieces
    #################################
    def GenerateRoot(self):
        if(hou.node("/obj/FBX_RESULT") == None):
            self.nodeSubnet = hou.node("/obj").createNode("subnet", "FBX_RESULT")
        else:
            self.nodeSubnet = hou.node("/obj/FBX_RESULT")

    #################################
    #Creates the initial geo nodes
    #for the pieces
    #################################
    def GenerateGeo(self):
        for objectToProcess in range(0, len(self.nodeDisplay)):
            self.nodePieces.append([])

            for index in range(0, self.numberOfPieces[objectToProcess]):
                #TODO: Append name to each geo node
                tempName = self.nodeDisplay[objectToProcess].parent().name()
                print tempName

                if(hou.node("/obj/FBX_RESULT/" + tempName + "_PIECE" + str(index)) == None):
                    self.nodePieces[objectToProcess].insert(index, self.nodeSubnet.createNode("geo", tempName + "_PIECE" + str(index)))
                else:
                    self.nodePieces[objectToProcess].insert(index, hou.node("/obj/FBX_RESULT/" + tempName + "_PIECE" + str(index)))

    #################################
    #Crawls the original geometry to
    #find the right object to use
    #for piece calculations
    #################################
    def FindReferenceGeometry(self):
        displayNodes = []

        for index in range(0, len(self.nodeGeo)):
            temp = self.nodeGeo[index].parm('soppath').unexpandedString()
            if 'opinputpath' in temp:
                temp = temp.split('"')[1::2][0]
            temp = self.nodeGeo[index].node(temp)

            referenceFound = False

            while(referenceFound == False):
                if(temp.geometry().findPrimAttrib('dopobject') != None):
                    temp = temp.inputs()[0]
                elif(temp.geometry() == None):
                    temp = temp.inputs()[0]
                else:
                    # return temp
                    displayNodes.append(temp)
                    break

        return displayNodes

    #################################
    #Modifies the created piece geo
    #nodes. A few nodes are added
    #with custom expressions.
    #################################
    def ModifyGeo(self):
        for objectToProcess in range(0, len(self.nodeDisplay)):
            # refGeo = self.FindReferenceGeometry()
            refGeo = self.nodeDisplay[objectToProcess]
            unpack = None
            deleteUnpack = None

            tempName = self.nodeDisplay[objectToProcess].parent().name()

            if(refGeo.parent().node("UNPACK")  == None):
                unpack = refGeo.parent().createNode("unpack", "UNPACK")
            elif (refGeo.parent().node("UNPACK")  != None):
                unpack = refGeo.parent().node("UNPACK")
            else:
                print "ERROR 0: Cannot generate unpack node!"

            unpack.setFirstInput(refGeo)

            for index in range(0, self.numberOfPieces[objectToProcess]):
                proxy   = None
                delete  = None
                xform   = None

                print self.nodePieces[objectToProcess][index]

                #TODO: Figure out order of operations
                #################################
                #Create the nodes to process the
                #individual pieces
                #################################
                if(hou.node("/obj/FBX_RESULT/" + tempName + "_PIECE" + str(index) + "/PROXY")  == None):
                    proxy = self.nodePieces[objectToProcess][index].createNode("object_merge", "PROXY")
                elif (hou.node("/obj/FBX_RESULT/" + tempName + "_PIECE" + str(index) + "/PROXY")  != None):
                    proxy = hou.node("/obj/FBX_RESULT/" + tempName + "_PIECE" + str(index) + "/PROXY")
                else:
                    print "ERROR 0: Cannot generate proxy node!"

                proxy.setParms({"objpath1":proxy.relativePathTo(unpack),
                                "xformtype":"object",
                                "xformpath":"../.."})

                if(hou.node("/obj/FBX_RESULT/" + tempName + "_PIECE" + str(index) + "/DELETE")  == None):
                    delete = self.nodePieces[objectToProcess][index].createNode("delete", "DELETE")
                elif (hou.node("/obj/FBX_RESULT/" + tempName + "_PIECE" + str(index) + "/DELETE")  != None):
                    delete = hou.node("/obj/FBX_RESULT/" + tempName + "_PIECE" + str(index) + "/DELETE")
                else:
                    print "ERROR 0: Cannot generate proxy node!"

                delete.setParms({'group':"@name=piece" + str(index),
                                'negate':'keep'})
                delete.setFirstInput(proxy)

                if(hou.node("/obj/FBX_RESULT/" + tempName + "_PIECE" + str(index) + "/XFORM")  == None):
                    xform = self.nodePieces[objectToProcess][index].createNode("xform", "XFORM")
                elif (hou.node("/obj/FBX_RESULT/" + tempName + "_PIECE" + str(index) + "/XFORM")  != None):
                    xform = hou.node("/obj/FBX_RESULT/" + tempName + "_PIECE" + str(index) + "/XFORM")
                else:
                    print "ERROR 0: Cannot generate proxy node!"


                #################################
                #This is important to grab the correct transform for the pieces.
                #Otherwise, all transforms will be at [0,0,0] and ruin your day.
                #The key here is finding the delta of the rest values between the
                #creation frame and the next frame.
                #################################
                xform.setFirstInput(delete)
                xform.parm('movecentroid').pressButton()

                #TODO: From event. Figure out calculations.
                creationFrame = self.nodeGeo[objectToProcess].parm('createframe').eval()
                hou.setFrame(creationFrame)
                dopxform1 = self.nodeGeo[objectToProcess].simulation().findObject(self.nodeGeo[objectToProcess].name()).geometry().iterPoints()[index].attribValue('rest')
                hou.setFrame(creationFrame+1)
                dopxform2 = self.nodeGeo[objectToProcess].simulation().findObject(self.nodeGeo[objectToProcess].name()).geometry().iterPoints()[index].attribValue('rest')
                deltaXFORM = []
                hou.setFrame(creationFrame)

                for i in range(0,3):
                    deltaXFORM.insert(i, dopxform1[i]-dopxform2[i])

                translates = [xform.parm('tx').eval(), xform.parm('ty').eval(), xform.parm('tz').eval()]
                result = [translates[0]+deltaXFORM[0], translates[1]+deltaXFORM[1], translates[2]+deltaXFORM[2]]
                result = []
                for i in range(0,3):
                    result.insert(i, translates[i]+deltaXFORM[i])

                xform.setParms({'tx':result[0],
                                'ty':result[1],
                                'tz':result[2]})

                #################################
                #File I/O. Saves a temp obj to reset the mesh/transform
                #################################
                # if(hou.node("/obj/FBX_RESULT/PIECE" + str(index) + "/FILE")  == None):
                #     file = self.nodePieces[index].createNode("file", "FILE")
                # elif (hou.node("/obj/FBX_RESULT/PIECE" + str(index) + "/FILE")  != None):
                #     file = hou.node("/obj/FBX_RESULT/PIECE" + str(index) + "/FILE")
                # else:
                #     print "ERROR 0: Cannot generate file node!"
                #
                # file.setParms({'filemode':'auto',
                #                 'file':'$HIP/tmp/temp_piece_' + str(index) + '.bgeo'})
                # file.setFirstInput(xform)

                #################################
                #Delete original file node
                #################################
                if(str(hou.node("/obj/FBX_RESULT/" + tempName + "_PIECE" + str(index) + "/file1")) != "None"):
                    hou.node("/obj/FBX_RESULT/" + tempName + "_PIECE" + str(index) + "/file1").destroy()

                self.ArrangeAllNodes(self.nodePieces[objectToProcess][index].path())

            self.ArrangeAllNodes("/obj")
            self.ArrangeAllNodes(self.nodeSubnet.path())


    #################################
    #Just to set the layouts
    #################################
    def ArrangeAllNodes(self, path):
        hou.node(path).layoutChildren()


    #################################
    #This crawls through the timeline and sets the keyframes for each piece
    #in the FBX_EXPORT subnet. This GREATLY saves on export time.
    #################################
    def ProcessMesh(self):
        RFSTART = int(hou.expandString('$RFSTART'))
        RFEND = int(hou.expandString('$RFEND'))


        for frame in range(RFSTART, RFEND+1):
            hou.setFrame(frame)
            # print "Processing Frame: " + str(frame)

            for objectToProcess in range(0, len(self.numberOfPieces)):
                for index in range(0,self.numberOfPieces[objectToProcess]):
                    for index_parm in range(0,3):
                        hou_keyed_parm = self.nodePieces[objectToProcess][index].parm(self.PARMS[index_parm])
                        hou_keyframe = hou.Keyframe()
                        hou_keyframe.setFrame(frame)
                        hou_keyframe.setValue(self.nodeGeo[objectToProcess].simulation().findObject(self.nodeGeo[objectToProcess].name()).geometry().iterPoints()[index].attribValue('P')[index_parm])
                        hou_keyed_parm.setKeyframe(hou_keyframe)

                    for index_parm in range(0,3):
                        hou_keyed_parm = self.nodePieces[objectToProcess][index].parm(self.PARMS[index_parm+3])
                        hou_keyframe = hou.Keyframe()
                        hou_keyframe.setFrame(frame)
                        hou_keyframe.setValue(hou.Quaternion(self.nodeGeo[objectToProcess].simulation().findObject(self.nodeGeo[objectToProcess].name()).geometry().iterPoints()[index].attribValue('orient')).extractEulerRotates()[index_parm])
                        hou_keyed_parm.setKeyframe(hou_keyframe)

        print "Processing Complete!"

    ######################################
    #MAIN
    ######################################
    def __init__(self):
        if self.CheckObject():
            self.GrabPieces()
            self.GenerateRoot()
            self.GenerateGeo()
            self.ModifyGeo()
            self.ProcessMesh()
        else:
            print "Select ONE RBD Object Import in the DOP Network"
