import threading
import random
from time import sleep
from math import sqrt,cos,sin,pi

from Tkinter import *
import tkMessageBox as messagebox
from ttk import *
from PIL import Image, ImageTk

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

from event import myEvent

win_size = '1100x600'
g_height = 600
g_width = 1100
qpktThreshold = 0
rpktThreshold = 0 
modes = [("Mitigation On", "On"),("Mitigation Off", "Off")]

class ControllerGui():
    def __init__(self, event, sw_mac, h_mac, topology):
        """ init 

        """
        self.event = event
        
        self.bg_tp = "black" 
        self.bg = "white"
        self.host_color = "white"
        self.sw_color = "white"
        self.r_color  = "#ffcc66"
        self.q_color  = "#B585BE"
        #self.ov_r_color = "red"
        #self.ov_q_color = "yellow"
        self.notice_color = "#5D5D5D"

        self.root = Tk()
        self.root.title("Controller GUI")
        self.root.geometry(win_size)

        TBgImage = Image.open('Img/top_bg.png').resize((1100,100), Image.ANTIALIAS)
        BBgImage = Image.open('Img/bottom_bg.png').resize((1100,100), Image.ANTIALIAS)
        TopoBgImage = Image.open('Img/gray_bg.png').resize((400,400), Image.ANTIALIAS)

        self.t_bgPhoto = ImageTk.PhotoImage(TBgImage)
        self.b_bgPhoto = ImageTk.PhotoImage(BBgImage)
        self.topo_bgPhoto = ImageTk.PhotoImage(TopoBgImage)


        self.fr_bg = Frame(self.root, height = g_height-100, width = g_width)
        self.fr_tp = Frame(self.fr_bg, height = 100, width = g_width)
        # self.fr_tb = Frame(self.fr_bg, height = g_height-100, width = g_width/2)
        
        self.cv_tp = Canvas(self.fr_bg, height = 100, width = g_width,highlightthickness=0)
        
        self.cv_tp.create_image(0,0, image=self.t_bgPhoto, anchor = "nw")
        
        self.cv_topo = Canvas(self.fr_bg,bg = self.bg, height = 400, width = 400,highlightthickness=0)
        self.cv_topo.create_image(0,0, image=self.topo_bgPhoto, anchor="nw")

        self.cv_table = Canvas(self.fr_bg,bg = self.bg, height = 400, width = 700,highlightthickness=0)

        self.cv_btm= Canvas(self.fr_tp, height = 100, width = g_width,highlightthickness=0)
        self.cv_btm.create_image(0,0, image=self.b_bgPhoto, anchor = "nw")
        

        self.fr_bg.pack()
        self.fr_tp.pack(side="bottom")
        # self.fr_tb.pack(side="right")

        self.fonts = ("arial", 12)

        self.var = StringVar()
        self.L1 = Label(self.fr_bg, textvariable=self.var, width=30, anchor="center")
        self.L1.place(x=85, y=470)

        self.thres = Label(self.fr_bg, text="Packet Threshold:", anchor="center", background=self.bg)
        self.thres.place(x=480, y=420)
        self.usrIn = StringVar()
        self.usrIn.set("")
        self.thresIn = Entry(self.fr_bg, textvariable=self.usrIn, width=5, font=self.fonts)
        self.thresIn.place(x=600, y=420)
        self.enter = Button(self.fr_bg, text="Enter", command=self.getThreshold)
        self.enter.place(x=655, y=420)

        self.tree = Treeview(self.root, columns=('col1', 'col2', 'col3', 'col4') ,show='headings')

        self.sw_mac = sw_mac
        self.h_mac = h_mac
        self.topology = topology

        self.ge_network()

        self.node_size = 10
        self.create_node()

        self.style = Style()
        quitImage = Image.open('Img/up_quit.png').resize((180,42), Image.ANTIALIAS)
        refreshImage = Image.open('Img/up_refresh.png').resize((180,42), Image.ANTIALIAS)

        b_quitImage = Image.open('Img/down_quit.png').resize((180,42), Image.ANTIALIAS)
        b_refreshImage = Image.open('Img/down_refresh.png').resize((180,42), Image.ANTIALIAS)

        # use self.quitPhoto
        self.quitPhoto = ImageTk.PhotoImage(quitImage) 
        self.refreshPhoto = ImageTk.PhotoImage(refreshImage) 
        self.b_quitPhoto = ImageTk.PhotoImage(b_quitImage) 
        self.b_refreshPhoto = ImageTk.PhotoImage(b_refreshImage) 

        self.style.configure("Q.TButton",
                # background="red", foreground="white", compound="left",
                background=self.bg,
                font=self.fonts, relief="flat", 
                image = self.quitPhoto, padding=0,
                )
        self.style.map("Q.TButton",
                background=[("active",self.bg)],
                image=[("active",self.b_quitPhoto)],
                )

        self.style.configure("R.TButton",
                # background="green", 
                background=self.bg,
                font=self.fonts, relief="flat", 
                image = self.refreshPhoto, padding=0)
        self.style.map("R.TButton",
                background=[("active",self.bg)],
                image=[("active",self.b_refreshPhoto)],
                )



        self.button_quit = Button(self.root, style="Q.TButton",command=self.quit
                # , compound="left"
                )
        self.button_quit.place(x=850, y=450)

        self.button_refresh = Button(self.root, style="R.TButton", command=self.refresh_network)
        self.button_refresh.place(x=850, y=400)

        self.cv_tp.pack(expand="Yes", side="top", fill="both",ipadx=0,ipady=0,padx=0,pady=0)
        self.cv_topo.pack(expand="Yes", anchor="center",side="left", fill="both")
        self.cv_table.pack(expand="Yes", anchor="center",side="right", fill="both")
        self.cv_btm.pack(expand="Yes", side="bottom", fill="both")
        #self.cv.pack()
        self.cv_topo.bind('<Motion>' , self.move_handler)
        self.cv_topo.bind('<Button-1>', self.click_handler)

        self.edgeWarn_th = threading.Thread(target=self.edge_traffic_warn, args=(self.event,self.topology, self.cv_topo))
        self.edgeWarn_th.setDaemon(True)
        self.edgeWarn_th.start()
        
        self.v = StringVar()
        self.on_off_xpos = 150
        self.on_off_ypos = 500

        for text, mode in modes:
            self.rate_set = Radiobutton(self.fr_bg, text=text, variable=self.v, value=mode, command=self.mitigation).place(x=self.on_off_xpos, y=self.on_off_ypos, anchor=W)
            self.on_off_ypos += 25

        self.root.mainloop()

    def ge_network(self):
        """ generate network """

        self.G = nx.Graph()
        pos = {}
        fixed = []
        connected_gw = []
        for port, node in self.event.node_links["s4"]:
            if node != "s5":
                connected_gw.append(node)

        myCos = lambda x: np.cos(np.deg2rad(x))
        mySin = lambda x: np.sin(np.deg2rad(x))
        for s, mac in sorted(self.sw_mac.items()):
            self.G.add_node(mac.encode('utf-8'))
            if s in connected_gw:
                pos[mac] = myCos(90+15.0*connected_gw.index(s)), mySin(90+15.0*connected_gw.index(s))
                fixed.append(mac)

        for h, mac in sorted(self.h_mac.items()):
            self.G.add_node(mac.encode('utf-8'))
            # pos[mac] = (0,int(h[1:])/15)
            # fixed.append(mac)

        edge = []
        for no, link in sorted(self.topology.items()):
            keys = link.keys()
            edge.append((keys[0],keys[1]))

        self.G.add_edges_from(edge)

        pos["00:00:00:04:15:00"] = (0.0,0)
        pos["00:00:00:05:15:00"] = (0.7,0)

        fixed.append("00:00:00:04:15:00")
        fixed.append("00:00:00:05:15:00")

        self.links = self.G.edges
        self.nodes = nx.spring_layout(self.G, pos=pos, fixed=fixed)
        # for node, pos in self.nodes.items():
            # if node not in ["00:00:00:05:15:00","00:00:00:02:15:00","00:00:00:03:15:00","00:00:00:00:02:02","00:00:00:00:03:03"] and pos[0] > 0.3:
            #     pos[0] = 0.6-pos[0]

        # print self.nodes["00:00:00:07:15:00"]

    def refresh_network(self):
        """ refresh network """

        self.G.clear()
        self.ge_network()

        self.cv_topo.delete("all")
        #self.cv.delete("all")
        self.event.cleanObjID()
        self.cv_topo.create_image(0,0, image=self.topo_bgPhoto, anchor="nw")
        self.create_node()

    def create_node(self):
        """ create node """
        #img_sw = Image.open("Img/switch.png").resize((40, 40), Image.ANTIALIAS)
        # img_ctr = Image.open("Img/controller.png").resize((40, 40), Image.ANTIALIAS)
        #img_host = Image.open("Img/host.png").resize((40, 40), Image.ANTIALIAS)
        # img_pkt = Image.open("Img/packet.png").resize((40, 40), Image.ANTIALIAS)
        #self.photo_sw = ImageTk.PhotoImage(img_sw)
        # self.photo_ctr = ImageTk.PhotoImage(img_ctr)
        #self.photo_host = ImageTk.PhotoImage(img_host)
        # self.photo_pkt = ImageTk.PhotoImage(img_pkt)

        for node, pos in self.nodes.items():
            pos[0] = (self.extend(pos[0], 'x')+2)*100
            pos[1] = (self.extend(pos[1], 'y')+2)*100

        for link in self.links:
            if self.event.getQR(link[0], link[1], 1) == 'q':
                # link[0] -> half : query
                No = self.cv_topo.create_line(
                        self.nodes[link[0]][0]+self.node_size/2, 
                        self.nodes[link[0]][1]+self.node_size/2,
                        (self.nodes[link[0]][0]+self.nodes[link[1]][0]+self.node_size)/2, 
                        (self.nodes[link[0]][1]+self.nodes[link[1]][1]+self.node_size)/2,
                        fill=self.q_color, arrow=LAST, width=2)
                self.event.putObjID(No, link[0], link[1])
                # link[1] -> half : response
                No = self.cv_topo.create_line(
                        self.nodes[link[1]][0]+self.node_size/2,
                        self.nodes[link[1]][1]+self.node_size/2,
                        (self.nodes[link[0]][0]+self.nodes[link[1]][0]+self.node_size)/2,
                        (self.nodes[link[0]][1]+self.nodes[link[1]][1]+self.node_size)/2,
                        fill=self.r_color, arrow=LAST, width=2)
                self.event.putObjID(No, link[0], link[1])
            elif self.event.getQR(link[0], link[1], 1) == 'r':
                # link[1] -> half : query
                No = self.cv_topo.create_line(
                        self.nodes[link[1]][0]+self.node_size/2,
                        self.nodes[link[1]][1]+self.node_size/2,
                        (self.nodes[link[0]][0]+self.nodes[link[1]][0]+self.node_size)/2,
                        (self.nodes[link[0]][1]+self.nodes[link[1]][1]+self.node_size)/2,
                        fill=self.q_color, arrow=LAST, width=2)
                self.event.putObjID(No, link[0], link[1])
                # link[0] -> half : response
                No = self.cv_topo.create_line(
                        self.nodes[link[0]][0]+self.node_size/2,
                        self.nodes[link[0]][1]+self.node_size/2,
                        (self.nodes[link[0]][0]+self.nodes[link[1]][0]+self.node_size)/2,
                        (self.nodes[link[0]][1]+self.nodes[link[1]][1]+self.node_size)/2,
                        fill=self.r_color, arrow=LAST, width=2)
                self.event.putObjID(No, link[0], link[1])

        self.switches = {}
        self.hosts = {}
        for node, pos in self.nodes.items():
            if node[15:] == "00" :
                # sw = self.cv.create_image(pos[0]+10, pos[1]+10, image=self.photo_sw)
                sw = self.cv_topo.create_oval(pos[0], pos[1], pos[0]+self.node_size, pos[1]+self.node_size, fill=self.sw_color)
                self.switches[node] = sw
            else:
                host = self.cv_topo.create_polygon(pos[0], pos[1], pos[0], pos[1]+self.node_size, pos[0]+self.node_size, pos[1]+self.node_size, pos[0]+self.node_size, pos[1], fill=self.host_color, outline="black")
                # host = self.cv.create_image(pos[0]+10, pos[1]+10, image=self.photo_host)
                self.hosts[node] = host

        #self.overlaplist = []
        #self.comparelist = []
        #for no, link in sorted(self.topology.items()):
        #    mac1 = link.keys()[0]
        #    mac2 = link.keys()[1]
        #    self.overlaplist.append(self.event.getObjID(mac1, mac2)[0])
        #    self.overlaplist.append(self.event.getObjID(mac1, mac2)[1])

        #self.comparelist = self.overlaplist
        #for Id in self.overlaplist:
        #    flag = 0
        #    if self.comparelist == None:
        #        break
        #    del self.comparelist[self.comparelist.index(Id)]
        #    pos = self.cv_topo.coords(Id)
        #    result = self.cv_topo.find_overlapping(pos)
        #    for x in self.comparelist:
        #        x_pos = self.cv_topo.coords(x)
        #        if x_pos in result:
        #            self.refresh_network()
        #            flag = 1
        #            break
        #    if flag == 1:
        #        break

    def extend(self, num, axis='x'):
        """ expand network size """
        return num
        # if num < 0:
            # num = abs(num)
            # return sqrt(num) * sqrt(2) * (-1)
        # else:
        #     return sqrt(num) * sqrt(2)

    def edge_traffic_warn(self, event, topology, cv_topo):
        """ detect which edge is busy, warn user via color changing """
        while event.is_set() is True:
            pktMax = 0
            edgeWidth_q = 2
            edgeWidth_r = 2
            for no, link in sorted(topology.items()):
                mac1 = link.keys()[0]
                mac2 = link.keys()[1]
                pktNum_q = event.getPktNum(mac1, mac2, 'q')
                pktNum_r = event.getPktNum(mac1, mac2, 'r')
                pktMax = pktNum_q if pktNum_q > pktMax else pktMax
                pktMax = pktNum_r if pktNum_r > pktMax else pktMax
                pktMax = 20 if pktMax < 20 else pktMax

                if pktNum_q <= qpktThreshold:
                    edgeWidth_q = (pktNum_q%5)+2
                    edgeWidth_q = 2 if edgeWidth_q < 2 else edgeWidth_q
                    cv_topo.itemconfig(event.getObjID(mac1, mac2)[0], fill=self.q_color, width=edgeWidth_q)
                elif pktNum_q > qpktThreshold:
                    edgeWidth_q = int(pktNum_q*20/pktMax)
                    edgeWidth_q = 7 if edgeWidth_q < 7 else edgeWidth_q
                    cv_topo.itemconfig(event.getObjID(mac1, mac2)[0], fill=self.edgeColorCtr(self.q_color, edgeWidth_q, "q"), width=edgeWidth_q)
                if pktNum_r <= rpktThreshold:
                    edgeWidth_r = (pktNum_q%5)+2
                    edgeWidth_r = 2 if edgeWidth_r < 2 else edgeWidth_r
                    cv_topo.itemconfig(event.getObjID(mac1, mac2)[1], fill=self.r_color, width=edgeWidth_r)
                elif pktNum_r > rpktThreshold:
                    edgeWidth_r = int(pktNum_r*20/pktMax)
                    edgeWidth_r = 7 if edgeWidth_r < 7 else edgeWidth_r
                    cv_topo.itemconfig(event.getObjID(mac1, mac2)[1], fill=self.edgeColorCtr(self.r_color, edgeWidth_r, "r"), width=edgeWidth_r)

            for i in range(0, 10):
                if event.is_set() is False:
                    break
                sleep(1)

    def edgeColorCtr(self, color, width, pkttype="q"):
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        if pkttype == "q":
            while width > 6:
                g -= 15
                width -= 2
        elif pkttype == "r":
            while width > 6:
                g -= 10
                b -= 10
                width -= 2
        return "#{0:02x}{1:02x}{2:02x}".format(r,g,b)

    def mitigation(self):
        if self.v.get() == "On":
            self.event.setMeterFlag(1)
            print "Mitigation is opened"
        elif self.v.get() == "Off":
            self.event.setMeterFlag(0)
            print "Mitigation is closed"

    def dbClick2ShowNode(self, event):
        """ click one row to show node position """
        for s_mac, pos in self.switches.items():
            self.cv_topo.itemconfig(self.switches[s_mac], fill=self.sw_color)
        for h_mac, pos in self.hosts.items():
            self.cv_topo.itemconfig(self.hosts[h_mac], fill=self.host_color)
        name = self.tree.item(self.tree.selection())['values'][0]
        if name == "DNS Server":
            name = "h3"
        elif name == "victim":
            name = "h1"
        elif name == "gateway sw":
            name = "s4"
        elif name == "router":
            name = "s5"
        mac = self.event.name2mac(name)
        if mac[15:] == "00":
            self.cv_topo.itemconfig(self.switches[mac], fill=self.notice_color)
        else:
            self.cv_topo.itemconfig(self.hosts[mac], fill=self.notice_color)

    def quit(self):
        #TODO clear others 
        self.G.clear()
        self.cv_topo.delete("all")
        #self.cv.delete("all")
        self.root.destroy()
        self.event.clear()
        # exit()

    def move_handler(self, event):
        """ detect if mouse is focus, show information """
        self.var.set('')
        
        for node, pos in self.nodes.items():
            if  pos[0] < event.x < pos[0]+self.node_size and pos[1] < event.y < pos[1]+self.node_size:
                name = self.event.mac2name(node)
                if node[15:] == "00" :
                    self.var.set(name+" : "+node)
                else:
                    self.var.set(name+" : "+node)
                break

    def click_handler(self, event):
        """ click one node to show information """
        if self.tree != None:
            x = self.tree.get_children()
            for item in x:
                self.tree.delete(item)
        for node, pos in self.nodes.items():
            if  pos[0] < event.x < pos[0]+self.node_size and pos[1] < event.y < pos[1]+self.node_size:
                for s_mac, pos in self.switches.items():
                    self.cv_topo.itemconfig(self.switches[s_mac], fill=self.sw_color)
                for h_mac, pos in self.hosts.items():
                    self.cv_topo.itemconfig(self.hosts[h_mac], fill=self.host_color)
                self.tree = Treeview(self.root, columns=('col1', 'col2', 'col3', 'col4') ,show='headings')
                self.tree.column('col1', width=100, anchor='center')
                self.tree.column('col2', width=70, anchor='center')
                self.tree.column('col3', width=75, anchor='center')
                self.tree.column('col4', width=75, anchor='center')
                self.tree.heading('col1', text='name')
                self.tree.heading('col2', text='port')
                self.tree.heading('col3', text='pkt_q')
                self.tree.heading('col4', text='pkt_r')

                inf = self.event.getNodeInf(node)

                for i in inf:
                   self.tree.insert('', 'end', values=i)

                self.ybar = Scrollbar(self.root, orient=VERTICAL, command=self.tree.yview)
                self.tree.configure(yscrollcommand=self.ybar.set)
                self.tree.place(x=480, y=170)
                self.ybar.place(x=800, y=170, height=218)

                self.tree.bind("<Double-1>", self.dbClick2ShowNode)

    def getThreshold(self):
        try:
            int(self.usrIn.get())
        except ValueError:
            self.usrIn.set("")
            messagebox.showerror("Error", "You enter the wrong type !!\nPlease enter a number with type \"int\"")
        else:
            if 0 <= int(self.usrIn.get()) <= 1000:
                self.event.thr_res_num = self.usrIn.get()
                qpktThreshold = self.usrIn.get()
                rpktThreshold = self.usrIn.get()
                print "You change the threshold to " + str(self.event.thr_res_num)
            else:
                self.usrIn.set("")
                messagebox.showwarning("Warning", "Please enter a number which value is between 0 to 1000 (both includiing) !!")

def main():

    sw_mac = {'s16': '00:00:00:10:15:00', 's9': '00:00:00:09:15:00', 's8': '00:00:00:08:15:00', 's17': '00:00:00:11:15:00', 's3': '00:00:00:03:15:00', 's2': '00:00:00:02:15:00', 's1': '00:00:00:01:15:00', 's10': '00:00:00:0a:15:00', 's7': '00:00:00:07:15:00', 's6': '00:00:00:06:15:00', 's5': '00:00:00:05:15:00', 's4': '00:00:00:04:15:00', 's13': '00:00:00:0d:15:00', 's20': '00:00:00:14:15:00', 's18': '00:00:00:12:15:00', 's15': '00:00:00:0f:15:00', 's12': '00:00:00:0c:15:00', 's19': '00:00:00:13:15:00', 's21': '00:00:00:15:15:00', 's14': '00:00:00:0e:15:00', 's11': '00:00:00:0b:15:00'}
    
    h_mac = {u'h8': u'00:00:00:00:0c:08', u'h9': u'00:00:00:00:0d:09', u'h7': u'00:00:00:00:0b:07', u'h1': u'00:00:00:00:01:01', u'h6': u'00:00:00:00:0a:06', u'h12': u'00:00:00:00:10:0c', u'h13': u'00:00:00:00:12:0d', u'h14': u'00:00:00:00:13:0e', u'h15': u'00:00:00:00:15:0f', u'h4': u'00:00:00:00:07:04', u'h5': u'00:00:00:00:08:05', u'h10': u'00:00:00:00:0e:0a', u'h2': u'00:00:00:00:02:02', u'h11': u'00:00:00:00:0f:0b', u'h3': u'00:00:00:00:03:03'}
    topology = {'24': {'00:00:00:05:15:00': 3, '00:00:00:04:15:00': 10}, '25': {'00:00:00:0d:15:00': 2, '00:00:00:04:15:00': 3}, '26': {'00:00:00:0e:15:00': 2, '00:00:00:04:15:00': 4}, '27': {'00:00:00:11:15:00': 2, '00:00:00:04:15:00': 7}, '20': {'00:00:00:07:15:00': 2, '00:00:00:04:15:00': 12}, '21': {'00:00:00:06:15:00': 2, '00:00:00:04:15:00': 11}, '22': {'00:00:00:08:15:00': 2, '00:00:00:04:15:00': 13}, '23': {'00:00:00:09:15:00': 2, '00:00:00:04:15:00': 14}, '28': {'00:00:00:0f:15:00': 2, '00:00:00:04:15:00': 5}, '29': {'00:00:00:04:15:00': 9, '00:00:00:14:15:00': 2}, '1': {u'00:00:00:00:12:0d': 1, '00:00:00:12:15:00': 1}, '0': {'00:00:00:13:15:00': 1, u'00:00:00:00:13:0e': 1}, '3': {'00:00:00:0d:15:00': 1, u'00:00:00:00:0d:09': 1}, '2': {'00:00:00:08:15:00': 1, u'00:00:00:00:08:05': 1}, '5': {'00:00:00:01:15:00': 1, u'00:00:00:00:01:01': 1}, '4': {u'00:00:00:00:0c:08': 1, '00:00:00:0c:15:00': 1}, '7': {'00:00:00:07:15:00': 1, u'00:00:00:00:07:04': 1}, '6': {'00:00:00:0a:15:00': 1, u'00:00:00:00:0a:06': 1}, '9': {u'00:00:00:00:0f:0b': 1, '00:00:00:0f:15:00': 1}, '8': {u'00:00:00:00:10:0c': 1, '00:00:00:10:15:00': 1}, '11': {u'00:00:00:00:03:03': 1, '00:00:00:03:15:00': 1}, '10': {'00:00:00:0e:15:00': 1, u'00:00:00:00:0e:0a': 1}, '13': {u'00:00:00:00:02:02': 1, '00:00:00:02:15:00': 1}, '12': {u'00:00:00:00:15:0f': 1, '00:00:00:15:15:00': 1}, '15': {'00:00:00:01:15:00': 2, '00:00:00:06:15:00': 1}, '14': {u'00:00:00:00:0b:07': 1, '00:00:00:0b:15:00': 1}, '17': {'00:00:00:05:15:00': 2, '00:00:00:03:15:00': 2}, '16': {'00:00:00:05:15:00': 1, '00:00:00:02:15:00': 2}, '19': {'00:00:00:04:15:00': 1, '00:00:00:0b:15:00': 2}, '18': {'00:00:00:04:15:00': 2, '00:00:00:0c:15:00': 2}, '31': {'00:00:00:13:15:00': 2, '00:00:00:04:15:00': 8}, '30': {'00:00:00:10:15:00': 2, '00:00:00:04:15:00': 6}, '34': {'00:00:00:14:15:00': 1, '00:00:00:15:15:00': 2}, '33': {'00:00:00:11:15:00': 1, '00:00:00:12:15:00': 2}, '32': {'00:00:00:0a:15:00': 2, '00:00:00:09:15:00': 1}}
    direction = {'24': {'00:00:00:05:15:00': 'r', '00:00:00:04:15:00': 'q'}, '25': {'00:00:00:0d:15:00': 'q', '00:00:00:04:15:00': 'r'}, '26': {'00:00:00:0e:15:00': 'q', '00:00:00:04:15:00': 'r'}, '27': {'00:00:00:11:15:00': 'q', '00:00:00:04:15:00': 'r'}, '20': {'00:00:00:07:15:00': 'q', '00:00:00:04:15:00': 'r'}, '21': {'00:00:00:06:15:00': 'q', '00:00:00:04:15:00': 'r'}, '22': {'00:00:00:08:15:00': 'q', '00:00:00:04:15:00': 'r'}, '23': {'00:00:00:09:15:00': 'q', '00:00:00:04:15:00': 'r'}, '28': {'00:00:00:0f:15:00': 'q', '00:00:00:04:15:00': 'r'}, '29': {'00:00:00:04:15:00': 'r', '00:00:00:14:15:00': 'q'}, '1': {'00:00:00:12:15:00': 'r', u'00:00:00:00:12:0d': 'q'}, '0': {'00:00:00:13:15:00': 'r', u'00:00:00:00:13:0e': 'q'}, '3': {'00:00:00:0d:15:00': 'r', u'00:00:00:00:0d:09': 'q'}, '2': {'00:00:00:08:15:00': 'r', u'00:00:00:00:08:05': 'q'}, '5': {'00:00:00:01:15:00': 'r', u'00:00:00:00:01:01': 'q'}, '4': {u'00:00:00:00:0c:08': 'q', '00:00:00:0c:15:00': 'r'}, '7': {'00:00:00:07:15:00': 'r', u'00:00:00:00:07:04': 'q'}, '6': {'00:00:00:0a:15:00': 'r', u'00:00:00:00:0a:06': 'q'}, '9': {u'00:00:00:00:0f:0b': 'q', '00:00:00:0f:15:00': 'r'}, '8': {u'00:00:00:00:10:0c': 'q', '00:00:00:10:15:00': 'r'}, '11': {u'00:00:00:00:03:03': 'r', '00:00:00:03:15:00': 'q'}, '10': {'00:00:00:0e:15:00': 'r', u'00:00:00:00:0e:0a': 'q'}, '13': {'00:00:00:02:15:00': 'r', u'00:00:00:00:02:02': 'q'}, '12': {'00:00:00:15:15:00': 'r', u'00:00:00:00:15:0f': 'q'}, '15': {'00:00:00:01:15:00': 'q', '00:00:00:06:15:00': 'r'}, '14': {u'00:00:00:00:0b:07': 'q', '00:00:00:0b:15:00': 'r'}, '17': {'00:00:00:05:15:00': 'q', '00:00:00:03:15:00': 'r'}, '16': {'00:00:00:05:15:00': 'r', '00:00:00:02:15:00': 'q'}, '19': {'00:00:00:04:15:00': 'r', '00:00:00:0b:15:00': 'q'}, '18': {'00:00:00:04:15:00': 'r', '00:00:00:0c:15:00': 'q'}, '31': {'00:00:00:13:15:00': 'q', '00:00:00:04:15:00': 'r'}, '30': {'00:00:00:10:15:00': 'q', '00:00:00:04:15:00': 'r'}, '34': {'00:00:00:14:15:00': 'r', '00:00:00:15:15:00': 'q'}, '33': {'00:00:00:11:15:00': 'r', '00:00:00:12:15:00': 'q'}, '32': {'00:00:00:0a:15:00': 'q', '00:00:00:09:15:00': 'r'}}
    node_links = {u'h8': [[1, 's12']], u'h9': [[1, 's13']], u'h2': [[1, 's2']], u'h3': [[1, 's3']], u'h1': [[1, 's1']], u'h6': [[1, 's10']], u'h7': [[1, 's11']], u'h4': [[1, 's7']], u'h5': [[1, 's8']], 's9': [[2, 's4'], [1, 's10']], 's8': [[2, 's4'], [1, u'h5']], 's3': [[1, u'h3'], [2, 's5']], 's2': [[1, u'h2'], [2, 's5']], 's1': [[1, u'h1'], [2, 's6']], 's7': [[2, 's4'], [1, u'h4']], 's6': [[1, 's1'], [2, 's4']], 's5': [[2, 's3'], [1, 's2'], [3, 's4']], 's4': [[2, 's12'], [3, 's13'], [5, 's15'], [4, 's14'], [12, 's7'], [13, 's8'], [14, 's9'], [1, 's11'], [6, 's16'], [7, 's17'], [10, 's5'], [11, 's6'], [9, 's20'], [8, 's19']], 's19': [[1, u'h14'], [2, 's4']], 's18': [[1, u'h13'], [2, 's17']], 's13': [[2, 's4'], [1, u'h9']], 's12': [[2, 's4'], [1, u'h8']], 's11': [[2, 's4'], [1, u'h7']], 's10': [[1, u'h6'], [2, 's9']], 's17': [[2, 's4'], [1, 's18']], 's16': [[2, 's4'], [1, u'h12']], 's15': [[2, 's4'], [1, u'h11']], 's14': [[2, 's4'], [1, u'h10']], u'h10': [[1, 's14']], u'h11': [[1, 's15']], u'h12': [[1, 's16']], u'h13': [[1, 's18']], u'h14': [[1, 's19']], u'h15': [[1, 's21']], 's20': [[2, 's4'], [1, 's21']], 's21': [[1, u'h15'], [2, 's20']]}
    event = myEvent(topology, direction, node_links)
    event.recordName(h_mac, sw_mac)
    c = ControllerGui(event, sw_mac, h_mac, topology)
if __name__ == '__main__':
    main()
