import json



async def process_websocket_event(websocket,packet,eventName,state):
    # print(packet)

    # this even is when a client asks for and the server gives, the list of devices that includes name and state        
    if eventName == "request_list_basic_devices":
        output_dict = {}
        output_dict["device_table"] = []
        for basic_dev in state["list_of_basicDevs"]:
            device_home = basic_dev.get_device_home()
            device_name = basic_dev.get_device_name()
            device_state = basic_dev.get_device_state()
            service_name = basic_dev.get_service_name()
            output_dict["device_table"].append( [device_home,device_name,device_state,service_name] )
        await sendPacketToWSClient(websocket,"give_list_basic_devices",output_dict)

