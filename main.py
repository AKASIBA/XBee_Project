# 巻上げ制御
import binascii
import xbee
import machine
import uio
import os
import time

ON = 5
OFF = 4
addr_coordinator = '\x00\x00\x00\x00\x00\x00\x00\x00'
xbee.atcmd('ID', 0x480)  # pan_id 480
xbee.atcmd('AV', 0x00)  # ADC_reference_1.25V
temp = machine.ADC('D1')
sl = str(binascii.hexlify(xbee.atcmd('SL')))[6:-1]
print(sl)
time.sleep(2)

drv = ["""&{'temp':'25','o_time':'07:00','c_time':'16:00','select':'00',wall:'00','everyday':'00',\
       'remote':'00','button':'01'}"""]
drv.append("""<body><h1><strong>くるファミ　AceDX</strong></h1><form name="Form" method="POST"></form>\
              <input name="cont_dev" value='""" + sl + """' hidden>""")
drv.append("""<p><input type="radio" id="select1" name="select" value='01' onClick="selectflg1(this.checked);"> 手動\
        <input type="radio" id="select2" name="select"  value='02'onClick="selectflg2(this.checked);"> 自動</p>""")
drv.append("""<fieldset id="selected1" disabled="disabled"><legend> 手動 </legend>\
    <p><button class="button" name="button" value='02' type="submit" id="button"><strong>開</strong></button>""")
drv.append("""<button class="button" name="button" value='03' type="submit" id="button"><strong>閉</strong></button>\
    <button class="button" name="button" value='04' type="submit" id="button"><strong>停止</strong></button></p></fieldset>""")
drv.append("""<fieldset id="selected2" disabled="disabled"><legend> 自動 </legend><p><input type="radio" name="wall" value="01">\
              温度制御<input type="radio" name="wall" value="02"> 時間制御</p>""")
drv.append("""<p>設定温度<input type="number" name="temp" value= $ min="0" max="35"> ℃</p>""")
drv.append("""<p><label>開く時刻  : <input type="time" id='time' name='o_time' value= $ required></p>\
              <p><label>閉る時刻  : <input type="time" id='time' name='c_time' value= $ required></p>""")
drv.append("""<p><label>毎日同時刻に実行 :<input type="checkbox" name="everyday" id="text" value='01' ></label></p>""")
drv.append("""<p><label>リモート操作有効 :<input type="checkbox" name="remote" id="text" value='01'> </label></p>\
    <p><button class="button" name="button" value='01' type="submit" id="button"><strong>実行</strong></button></p>""")
drv.append("""</fieldset><br><button class="button" name="control" value='CANCEL' type="submit" id="button"><strong>戻る\
           </strong></button>""")
drv.append("""<script>
        function selectflg1(ischecked){\
          if(ischecked == true){\
          document.getElementById("selected1").disabled = false;\
          document.getElementById("selected2").disabled = true;\
          } else {""")
drv.append("""document.getElementById("selected1").disabled = true;\
          document.getElementById("selected2").disabled = false; }}""")
drv.append("""function selectflg2(ischecked){\
          if(ischecked == true){\
            document.getElementById("selected2").disabled = false;\
            document.getElementById("selected1").disabled = true;\
          } else {""")
drv.append("""document.getElementById("selected2").disabled = true;\
            document.getElementById("selected1").disabled = false;}}</script></body></html>""")
drv.append('?')
drv.append(""">exe_dict['temp'] = '{:0>2}'.format(form.getvalue('temp')) if form.getvalue('temp')@@""")
drv.append(""">exe_dict['o_time'] = '{:0>2}'.format(form.getvalue('o_time')) if form.getvalue('o_time')@@\
               exe_dict['c_time'] = '{:0>2}'.format(form.getvalue('c_time')) if form.getvalue('c_time')@@""")
drv.append("""">exe_dict['select'] = '{:0>2}'.format(form.getvalue('select')) if form.getvalue('select') else '00'@@\
                exe_dict['wall'] = '{:0>2}'.format(form.getvalue('wall')) if form.getvalue('wall') else '00'@@""")
drv.append(
    """>exe_dict['everyday'] = '{:0>2}'.format(form.getvalue('everyday')) if form.getvalue('everyday')else '00' @@""")
drv.append(""">exe_dict['remote'] = '{:0>2}'.format(form.getvalue('remote')) if form.getvalue('remote') else '00'@@""")
drv.append(""">if 'button' in form:exe_dict['button'] = '{:0>2}'.format(form.getvalue('button'))@@""")
drv.append('@')


def pin_ini():
    xbee.atcmd('d2', OFF)
    xbee.atcmd('d3', OFF)
    xbee.atcmd('d6', OFF)


def packet_receive(com):
    packet = xbee.receive()
    if packet:
        payload = str(packet['payload'].decode('utf-8'))
    else:
        payload = com
    return payload


def send_driver():
    print('install_command')
    for i in drv:
        print(i)
        xbee.transmit(addr_coordinator, i)
        time.sleep_ms(100)
    print('send!')


def main():
    xbee.transmit(addr_coordinator, 'S')
    pin_ini()
    now_time = 0
    s_time = 0
    p_time = 0
    temp_c = ''
    o_time = ''
    c_time = ''
    select = ''
    wall = ''
    everyday = ''
    remote = ''
    button = ''
    d = True
    t0 = 0
    s_w = 0
    mes_c = ''
    conf = ''
    c = 0
    try:
        f = uio.open('conf.txt', mode='r')
        conf = f.read()
        f.close()
        c = 1
    except OSError as e:
        print(e)
    print(conf)
    while True:
        t = time.ticks_ms()
        if t0 <= t or t0 - t >= 3000:  #
            t0 = t + 1000
            if now_time >= 86400:
                now_time = 0
                p_time = 0
            now_time = now_time + 1
            s_w = 0
            s_time = int(now_time / 60)
        temp_a = temp.read() * 0.030525 - 48.3
        command = packet_receive(conf)
        if command:
            print(command)
            if command == 'sibainu':
                send_driver()
            else:
                temp_c = int(command[0:2])
                o_time = int(command[2:4]) * 60 + int(command[5:7])
                c_time = int(command[7:9]) * 60 + int(command[10:12])
                select = command[12:14]
                wall = command[14:16]
                everyday = command[16:18]
                remote = command[18:20]
                button = command[20:22]
                now_time = int(command[-6:])
                s_time = int(now_time / 60)
                d = True
            if conf:
                command = conf
                conf = ''
                if c == 0:
                    try:
                        os.remove('conf.txt')
                    except OSError as e:
                        print(e)
                    f = uio.open('conf.txt', mode='w')
                    f.write(command)
                    f.close()
            if remote == '01':
                xbee.atcmd('d6', ON)
                mes_c = 'リモート　ON'
                if select == '01':
                    if button == '02':
                        xbee.atcmd('d3', OFF)
                        xbee.atcmd('d2', ON)
                    elif button == '03':
                        xbee.atcmd('d2', OFF)
                        xbee.atcmd('d3', ON)
                    elif button == '04':
                        xbee.atcmd('d2', OFF)
                        xbee.atcmd('d3', OFF)
                else:
                    if wall == '01':
                        mes_c = "C0100001巻上温度:" + temp_c + '℃'
                        if temp_c <= temp_a:  # 後で時間設定記述
                            xbee.atcmd('d3', OFF)
                            xbee.atcmd('d2', ON)
                            time.sleep(5)
                            xbee.atcmd('d2', OFF)
                        if temp_c >= temp_a + 5:  # ヒステリシス　5
                            xbee.atcmd('d2', OFF)
                            xbee.atcmd('d3', ON)
                            time.sleep(5)
                            xbee.atcmd('d3', OFF)
                    if wall == '02' and d:
                        mes_c = "C0100001巻上時間:" + '(' + command[2:7] + '-' + command[7:12] + ')'
                        if o_time <= s_time <= c_time:
                            xbee.atcmd('d3', OFF)
                            xbee.atcmd('d2', ON)
                        if c_time <= s_time:
                            xbee.atcmd('d2', OFF)
                            xbee.atcmd('d3', ON)
                            if everyday == '01':
                                d = True
                            else:
                                d = False
                                mes_c = "C0100001リモート ON"
            else:
                xbee.atcmd('d6', OFF)
            c = 0
        if p_time <= now_time:
            p_time = now_time + 30
            mes_a = "{0:.1f}".format(temp_a) + '℃' + "\x00"
            print(mes_a, '-', s_time)
            mes_a = 'A01' + "{:05.1f}".format(temp_a) + '温度:' + mes_a
            print(mes_c)
            print(mes_a)
            try:
                xbee.transmit(addr_coordinator, mes_c)
                time.sleep(5)
                xbee.transmit(addr_coordinator, mes_a)
            except OSError as e:#siba
                print(e)

            if now_time == 35340 and s_w == 0:
                s_w = 1
                try:
                    xbee.transmit(addr_coordinator, 'S')
                    print('time calibration')
                except OSError as e:
                    print(e)


try:
    main()
except Exception as e:
    print(e)
    time.sleep(20)
    machine.reset()

