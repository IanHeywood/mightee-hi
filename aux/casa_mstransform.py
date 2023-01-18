import glob
import json
import os

with (open("aux/config.json")) as f:
	config = json.load(f)

mslist = glob.glob('*.ms')

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

	for band in ['LOW','MID','HIGH']:
		opdir = config[band]['band']
		if not os.path.isdir(opdir):
			os.mkdir(opdir)
		spw_selection = config[band]['spw_selection']
		opms = myms.replace('.ms','_'+target_name+'_'+band[1]+'.mms')
		print(opms)
		if band == 'LOW':
			average_chans = True
			chan_bin = 4
		else:
			average_chans = False
			chan_bin = 1
		mstransform(vis = myms,
			outputvis = opms,
			field = str(target_id),
			scan = scan_selection,
			spw = spw_selection,
			datacolumn = 'DATA',
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
			interpolation = 'nearest')