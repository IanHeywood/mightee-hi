import glob
import json
import os

with (open("aux/config.json")) as f:
	config = json.load(f)

mslist = glob.glob('*.ms')
CWD = os.getcwd()+'/'

for myms in mslist:

	tb.open(myms+'::FIELD')
	field_names = tb.getcol('NAME')
	tb.done()

	tb.open(myms+'::STATE')
	states = tb.getcol('OBS_MODE').tolist()
	target_state = states.index('TARGET')
	tb.done()

	tb.open(myms)
	subtab = tb.query(query='STATE_ID=='+str(target_state))
	target_id = list(set(subtab.getcol('FIELD_ID')))[0]
	target_name = field_names[target_id]
	target_scans = list(set(subtab.getcol('SCAN_NUMBER')))
	tb.done()

	scan_selection = ','.join(str(tt) for tt in target_scans)

	for band in ['L2','L1','L3']:
		opdir = config[band]['band']
		if not os.path.isdir(opdir):
			os.mkdir(opdir)
		for item in ['01_process_mms.py','02_image_channels.py','generators.py','aux']:
			syscall = 'ln -s '+CWD+item+' '+opdir+'/'+item
			os.system(syscall)
		spw_selection = str(config[band]['spw_selection'])
		opms = opdir+'/'+myms.replace('.ms','_'+target_name+'_'+band+'.mms')
		print(opms)
		if band == 'L1':
			average_chans = True
			chan_bin = 4
		else:
			average_chans = False
			chan_bin = 1
		mstransform(vis = myms,
			outputvis = str(opms),
			field = str(target_id),
			scan = str(scan_selection),
			spw = str(spw_selection),
			datacolumn = str(config['DATACOL']),
			usewtspectrum = True,
			realmodelcol = True,
			chanaverage = average_chans,
			chanbin = chan_bin,
			createmms = True,
			separationaxis = 'scan',
			numsubms = len(target_scans),
			hanning = False,
			regridms = True,
			mode = 'channel',
			outframe = 'BARY',
			interpolation = 'linear')