/**
 *  Copyright 2016 Ryan Finnie
 *
 *  Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
 *  in compliance with the License. You may obtain a copy of the License at:
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
 *  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License
 *  for the specific language governing permissions and limitations under the License.
 *
 */

import groovy.json.JsonOutput

metadata {
	definition (name: "TP-LINK Smart Plug HS100 (LAN web proxy)", namespace: "rfinnie", author: "Ryan Finnie") {
		capability "Actuator"
		capability "Refresh"
		capability "Switch"
	}

	tiles(scale: 2) {
		multiAttributeTile(name:"switch", type: "lighting", width: 6, height: 4, canChangeIcon: true){
			tileAttribute ("device.switch", key: "PRIMARY_CONTROL") {
				attributeState "on", label:'${name}', action:"switch.off", icon:"st.switches.light.on", backgroundColor:"#79b821", nextState:"turningOff"
				attributeState "off", label:'${name}', action:"switch.on", icon:"st.switches.light.off", backgroundColor:"#ffffff", nextState:"turningOn"
				attributeState "turningOn", label:'${name}', action:"switch.off", icon:"st.switches.light.on", backgroundColor:"#79b821", nextState:"turningOff"
				attributeState "turningOff", label:'${name}', action:"switch.on", icon:"st.switches.light.off", backgroundColor:"#ffffff", nextState:"turningOn"
			}
		}
		standardTile("refresh", "device.refresh", inactiveLabel: false, decoration: "flat", width: 2, height: 2) {
			state "default", label:"", action:"refresh.refresh", icon:"st.secondary.refresh"
		}
		main "switch"
		details(["switch", "refresh"])
	}
}

// Parse incoming device messages to generate events
def parse(String description) {
	//log.debug "description is $description"
	def msg = parseLanMessage(description)
	def status = msg.status
	def json = msg.json

	//log.debug("Values received: ${json}")
	if (json && json.system && json.system.get_sysinfo) {
		def thestate = (json.system.get_sysinfo.relay_state == 1 ? "on" : "off")
		log.debug "Outlet is $thestate"
		sendEvent(name: "switch", value: thestate)
		updateDataValue("model", json.system.get_sysinfo.model)
		updateDataValue("dev_name", json.system.get_sysinfo.dev_name)
		updateDataValue("alias", json.system.get_sysinfo.alias)
		updateDataValue("mac", json.system.get_sysinfo.mac)
		updateDataValue("type", json.system.get_sysinfo.type)
		updateDataValue("fwId", json.system.get_sysinfo.fwId)
		updateDataValue("hw_ver", json.system.get_sysinfo.hw_ver)
		updateDataValue("hwId", json.system.get_sysinfo.hwId)
		updateDataValue("sw_ver", json.system.get_sysinfo.sw_ver)
		updateDataValue("oemId", json.system.get_sysinfo.oemId)
		updateDataValue("deviceId", json.system.get_sysinfo.deviceId)
	}
}

private Integer convertHexToInt(hex) {
	Integer.parseInt(hex,16)
}

private String convertHexToIP(hex) {
	//log.debug("Convert hex to ip: $hex") 
	[convertHexToInt(hex[0..1]),convertHexToInt(hex[2..3]),convertHexToInt(hex[4..5]),convertHexToInt(hex[6..7])].join(".")
}

private String convertIPtoHex(ipAddress) { 
	String hex = ipAddress.tokenize( '.' ).collect { String.format( '%02x', it.toInteger() ) }.join()
	//log.debug "IP address entered is $ipAddress and the converted hex code is $hex"
	return hex

}

private String convertPortToHex(port) {
	String hexport = port.toString().format( '%04x', port.toInteger() )
	//log.debug hexport
	return hexport
}

private getHostAddress() {
	//return "10.9.8.1:8362"
	def parts = device.deviceNetworkId.split(":")
	//log.debug device.deviceNetworkId
	def ip = convertHexToIP(parts[0])
	def port = convertHexToInt(parts[1])
	return ip + ":" + port
}

def off() {
	log.debug "Turning outlet off"
	def json = JsonOutput.toJson([
		system: [
			set_relay_state: [
				state: 0,
			],
			get_sysinfo: [
				state: null,
			]
		]
	])
	def result = new physicalgraph.device.HubAction(
		method: "POST",
		path: "/command",
		body: json,
		headers: [
			HOST: getHostAddress(),
			"Content-Type": "application/json",
		]
	)
	return result
}

def on() {
	log.debug "Turning outlet on"
	def json = JsonOutput.toJson([
		system: [
			set_relay_state: [
				state: 1,
			],
			get_sysinfo: [
				state: null,
			]
		]
	])
	def result = new physicalgraph.device.HubAction(
		method: "POST",
		path: "/command",
		body: json,
		headers: [
			HOST: getHostAddress(),
			"Content-Type": "application/json",
		]
	)
	return result
}

def refreshHandler() {
	sendHubCommand(refresh())
}

def refresh() {
	//def hosthex = convertIPtoHex("10.9.8.1")
	//def porthex = convertPortToHex(8362)
	//device.deviceNetworkId = "$hosthex:$porthex" 

	def json = JsonOutput.toJson([
		system: [
			get_sysinfo: [
				state: null,
			]
		]
	])
	def result = new physicalgraph.device.HubAction(
		method: "POST",
		path: "/command",
		body: json,
		headers: [
			HOST: getHostAddress(),
			"Content-Type": "application/json",
		]
	)
	return result
}

def ping() {
	refresh()
}

def installed() {
	initialize()
}

def updated() {
	initialize()
}

def initialize() {
	unschedule()
	runEvery5Minutes(refreshHandler)
}

