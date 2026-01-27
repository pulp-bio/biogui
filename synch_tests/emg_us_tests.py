#!/usr/bin/env python
# coding: utf-8

# # Data Synchronization

# Updated on: 09.01.2025 </br>
# 
# Main changes: New Synchronization Method between EMG and Ultrasound, tests conducted with oscilloscope.
# 
# Protocol: sending a pulse evert 10 seconds, to detect if there is a mis-alignment over time

# In[1]:


import sys

sys.path.append(r'C:\Users\giusy\OneDrive\Desktop\HGR\manus-acquisition\data_synchronization')
from biogui_utils import *
from pathlib import Path

import matplotlib.pyplot as plt


# In[2]:


data_directory = Path(r"C:\Users\giusy\OneDrive\Desktop\HGR\biogui\synch_tests")


# In[3]:


acq_names =  ["2025-01-09_18-36-01",     # pulse 5ms width at random times (wulpus USB powered)
              "2025-01-10_08-46-21",    # move away from the dongle (battery)
              "2025-01-10_09-49-49",    # close to dongle --> move away --> close       
            "2025-01-10_10-07-29",      # close as in 0
            "2025-01-10_11-09-22",      # protocol rep 1, latopt not connected to power
            "2025-01-10_11-17-01",      #protocol rep2, laptop connected to power
            "2025-01-10_11-32-26",      # protocol without utting away, after power cycling everythin
            "2025-01-10_11-44-12",      # pulkses every 10 seconds, WULPUS USB powered. Acquisitions stopped before
            "2025-01-10_11-51-47",      #pulses every 10 seconds close to dongle, WULPUS USB powered. Laptop powered, WULPUS run till the end (4000  acqu)--> seems to be okay
            "2025-01-10_12-01-25",      # same as before, close to dongle, WULPUS battery powered, laptop powered, WULPUS runs til the end (4000 acq) --> okay
            "2025-01-10_12-05-27",       # same as before, close to dongle, WULPUS battery powered, laptop not powered, WULPUS runs til the end (4000 acq)
            "2025-01-10_12-11-40",      # protocol, wulpus battery powered, latopt not powered, wulus runs till the end
            "2025-01-10_12-23-17"]      # 16000 acquisitions, always close to dongle --> worked

wulpus_files = ["wulpus_2025-01-09_18-36-01.npz",   # sine wave at random times 
                "wulpus_2025-01-10_08-46-21.npz", # distance 2m from input -> BLE losses 
                "wulpus_2025-01-10_09-49-49.npz", 
                "wulpus_2025-01-10_10-07-29.npz", 
                "wulpus_2025-01-10_11-09-22.npz", 
                "wulpus_2025-01-10_11-17-01.npz", 
                "wulpus_2025-01-10_11-32-26.npz", 
                "wulpus_2025-01-10_11-44-12.npz", 
                 "wulpus_2025-01-10_11-51-47.npz",
                 "wulpus_2025-01-10_12-01-25.npz", 
                 "wulpus_2025-01-10_12-05-27.npz", 
                 "wulpus_2025-01-10_12-11-40.npz", 
                 "wulpus_2025-01-10_12-23-17.npz"]
                       
                                         
#wulpus_num_acquisitions = 5000


# In[4]:


#acq_idx = len(wulpus_files)-1
#print(acq_idx)
acq_idx=1


# In[5]:


acq_name = acq_names[acq_idx]

print(f'Data main directory: {data_directory}')
emg_file = data_directory/f"emg_{acq_name}.bin"
wulpus_trigger = data_directory/f"triggerWulpus_{acq_name}.bin"
counter_file = data_directory/f"counter_{acq_name}.bin"


# In[6]:


# Create dataframe containing acquired EMG data
print('Processing EMG data...\n')
fs_emg = 500
if fs_emg is not None:
    print(f'EMG data sampled at: {fs_emg} Hz')
else:
    fs_emg = 500
    print(f'Using default EMG sampling rate: 500 Hz')

EMG_Dataset = EMG_dataset(emg_file, num_channels=8, trigger_gui=False, fs_emg=fs_emg, filter=True)
emg_df_raw = EMG_Dataset.emg_raw_df.reset_index()


emg_df_filt = EMG_Dataset.emg_filter_df.reset_index()
# Originally it increases every 2 ms, now set progressive indexes

emg_df = emg_df_raw



# In[7]:


plt.figure()
plt.plot(emg_df_raw['Ch1'])
#plt.plot(emg_df_filt['Ch1'], linestyle='--')





trans_idx = emg_df_raw['Ch1'].diff() 
idx_threhsold = 1000
emg_idx = trans_idx[trans_idx > 700].index
emg_idx


# In[9]:


emg_idx_effect = [emg_idx[0]]

for cnt_idx, curr_idx in enumerate(emg_idx[1:]):
    if curr_idx == emg_idx[cnt_idx] + 1:
        print(f'previous:{emg_idx[cnt_idx]}')
        print(f'current:{curr_idx}')
    else:
        print(f'First idx: {curr_idx}')
        emg_idx_effect.append(curr_idx)


# In[10]:


plt.figure()
plt.plot(emg_df_raw['Ch1'])
plt.plot(emg_idx_effect, emg_df_raw.loc[emg_idx_effect, 'Ch1'], marker='o', linestyle='none')


# In[11]:


emg_idx_effect

# we are sending a pulse every 10 seconds
# hence, we should expect a difference of 5000 samples between pulses
# we always get 10 samples more -> this is due to the fact that the ADS samples faster than we are expecting
np.diff(emg_idx_effect)



# In[12]:


def read_counter(filePath, trigger_gui=True):
    '''
    filePath: str
    Note: File Containing Counter for BIOGAP data
    '''
    # Read data
    with open(filePath, "rb") as f:
        nCh = struct.unpack("<I", f.read(4))[0]
        bSig = bytes(f.read())
    sig = np.frombuffer(bSig, dtype='float32').reshape(-1, nCh).T
    data = sig.T

    # Data Contains: Counter (updated every BLE packet - every 14 ms), Progressive Counter, 
    # Wulpus Counter (Not in use atm), Timestamps

    # Considering for now only the progressive counter, the trigger gui and the timestamps
    if trigger_gui == True:
        counter_df = pd.DataFrame()
        # If we keep the GUI open, counter doesn't start from 0
        # TODO: change the FW
        counter_df['EMG_counter_header'] = data[:, 0]
        counter_df["EMG_counter"] = data[:, 1] - data[0, 1]
        counter_df["Trigger_gui"] = data[:, -2]
        counter_df["Timestamp"] = data[:, -1]

    else:
        counter_df['EMG_counter_header'] = data[:, 0]
        counter_df = pd.DataFrame()
        counter_df["EMG_counter"] = data[:, 1] - data[0, 1]
        counter_df["Timestamp"] = data[:, -1]

        
    return counter_df


# In[13]:


## Extract file that contains the counter
counter_df = read_counter(counter_file, trigger_gui=True)


# In[14]:


counter_df['EMG_counter']


# In[15]:


counter_df['EMG_counter_header'].diff()!=0


# In[16]:


# check where the sequence restarts

# This filters the counter for every BLE packet (expected indexes to have an increase of 7 samples)
new_packet_locs = counter_df['EMG_counter_header'][counter_df['EMG_counter_header'].diff() !=0].iloc[1:]


# In[17]:


# We expect an increase of 7 

np.where(np.diff(new_packet_locs.index)!=7)


# In[18]:


np.diff(new_packet_locs.index)


# In[19]:


plt.figure()
plt.plot(counter_df['EMG_counter_header'])


# In[20]:


# Get the unique timestamps and their counts
unique_timestamps, counts = np.unique(emg_df['Timestamp'], return_counts=True)

# Initialize the reconstructed timestamp list
reconstructed_time = np.linspace(unique_timestamps[0] - 0.002*counts[0], unique_timestamps[0], counts[0])

# Start from the first unique timestamp minus a small step (for extrapolation if necessary)
prev_timestamp = reconstructed_time[-1]

# Loop through unique timestamps and interpolate
for i, (current_timestamp, count) in enumerate(zip(unique_timestamps[1:], counts[1:])):
    # Interpolate linearly between the previous last timestamp and the current unique timestamp
    interpolated = np.linspace(prev_timestamp, current_timestamp, count+1, endpoint=True)
    reconstructed_time = np.append(reconstructed_time, interpolated[1:])
    
    # Update the previous timestamp for the next iteration
    prev_timestamp = interpolated[-1]



# In[21]:


plt.figure()
plt.plot(unique_timestamps, counts)
plt.show()


# In[22]:


plt.figure()
plt.plot(np.diff(emg_df['Timestamp_reconstructed']))
plt.show()


# In[23]:


plt.figure()
plt.plot(emg_df['Timestamp_reconstructed'].iloc[:21], emg_df['Ch1'].iloc[:21])


# In[24]:


def read_trigger_wulpus_new(filePath, trigger_gui=True):
    '''
    filePath: str
    Note: we are WULPUS trigger synchronization signal
    '''
    # Read data
    with open(filePath, "rb") as f:
        nCh = struct.unpack("<I", f.read(4))[0]
        bSig = bytes(f.read())
    
    # Trigger Wulpus New stores in the MSB the Synchronization Signal 
    sig = np.frombuffer(bSig, dtype='float32').reshape(-1, nCh).T
    data = sig.T
    if trigger_gui == True:
    # Extracting also trigger information 
        columns = ["Trigger_Wulpus", "Trigger_gui", "Timestamp"]
        trigger_df = pd.DataFrame(data, columns=columns)

    else:
    # Extracting also trigger information 
        columns = ["Trigger_Wulpus", "Timestamp"]
        trigger_df = pd.DataFrame(data, columns=columns)
        
    return trigger_df


# In[25]:


trigger_wulpus_df = read_trigger_wulpus_new(wulpus_trigger, trigger_gui=False)


# In[26]:


trigger_wulpus_df


# In[27]:


np.diff(counter_df['EMG_counter'])


# In[28]:


emg_df = pd.concat((emg_df, trigger_wulpus_df['Trigger_Wulpus'], counter_df['EMG_counter']), axis=1)


# In[29]:


emg_df


# In[30]:


# Now, check EMG Ble losses
#Count BLE losses 
emg_losses= np.where(np.diff(emg_df['EMG_counter'])!=1)[0]
count_emg_losses = (len(emg_losses))
print(f"Lost:{count_emg_losses} BIOGAP packets")


# In[31]:


# 50 us samples -> 500 emg samples


# In[32]:


# Define Now Ultrasound locations
# We get a trigger Signal every 50 Ultrasound frames
wps_trigger_diff = emg_df['Trigger_Wulpus'].diff()             # note .diff() already takes into account the first element (set to NaN)
wulpus_50_locs = wps_trigger_diff!=0 
print(wulpus_50_locs)      


# In[ ]:





# In[33]:


idx_wulpus = wps_trigger_diff[wps_trigger_diff!=0].index.values
# add the initial index manually (change the FW to send first trigger at the first pulse and not after 50)
#idx_wulpus[0] = idx_wulpus[1] - 500
print(idx_wulpus)
if idx_wulpus[0] == 0:
    idx_wulpus = idx_wulpus[1:]


# In[34]:


idx_wulpus         # are the indices in the emg dataframe


# In[35]:


np.diff(idx_wulpus)


# In[36]:


np.mean(np.diff(idx_wulpus))


# In[37]:


# cut everthing after first wulpus frame
#emg_df = emg_df.loc[idx_wulpus[0]:, :]
# Reset the index such that we start from 0 for simplicity
#emg_df = emg_df.reset_index(drop=True)
#emg_df['index_from_0'] = emg_df.index.values - emg_df.index.values[0]
#emg_df


# In[38]:


plt.figure()
plt.plot(emg_df['Trigger_Wulpus'])
plt.plot(idx_wulpus, emg_df['Trigger_Wulpus'].loc[idx_wulpus], marker='o', linestyle='none')
plt.show()

# every idx wulpus (dot) corresponds to the 50th - 100th ... etc ultrasound frame 


# # Read Wulpus

# In[39]:


from US_dataset import *


# In[40]:


data = np.load(data_directory/wulpus_files[acq_idx])
acq_num_arr= data['acq_num_arr']

print(f'Max acq num arr:{np.max(acq_num_arr)}')
acquired_samples = np.where(acq_num_arr == np.max(acq_num_arr))[0][0]
expected_samples = np.max(acq_num_arr)

print(f'Acquired:{acquired_samples}')
print(f'Expected:{expected_samples}')
losts = expected_samples-acquired_samples
print(f'Lost:{losts}')
    
us_raw_data = data['data_arr']
us_raw_data = us_raw_data[:, :acquired_samples+1]
us_tx_idx_arr = data['tx_rx_id_arr']
us_tx_idx_arr = us_tx_idx_arr[:acquired_samples+1]
acq_num_arr = data['acq_num_arr'] [:acquired_samples+1]
print(f'last acq_num_arr:{acq_num_arr[-1]}')


# In[41]:


# the maximum index value should correspond to the last acquisition number array acquired 
# If we loose samples, the US data corresponding to this expected idx will be set to NaN
expected_idx = np.arange(acq_num_arr[-1]+1)
us_df = pd.DataFrame(index=expected_idx)

# assing data to the corresponding ultrasound frames
us_df.loc[acq_num_arr, 'Transducer'] = us_tx_idx_arr.astype(int)
# Assign 'Transducer_Data' column with arrays
us_raw_transp = us_raw_data.T
us_df.loc[acq_num_arr, 'Transducer_Data'] = pd.Series(list(us_raw_transp), index=acq_num_arr)


# In[42]:


expected_idx


# In[43]:


nan_locs = us_df[us_df['Transducer'].isna() == True].index

test_acquisitions = True
for curr_nan in nan_locs:
    # check the value of the transducer at previous location
    prev_trans = us_df.loc[curr_nan-1, 'Transducer']
    print(f'previous trans value: {prev_trans}')
    if test_acquisitions:
        missing_trans_idx = 0
    else:
        if prev_trans == 3:
            missing_trans_idx = 0
        else:
            missing_trans_idx = prev_trans + 1
    us_df.loc[curr_nan, 'Transducer'] = missing_trans_idx
    print(us_df.loc[curr_nan, 'Transducer'])


# In[44]:


# We will assign a NaN value wherever we have data losses
print(len(us_df[us_df['Transducer_Data'].isna() == True]))


# In[45]:


us_df[us_df[us_df['Transducer']==0]['Transducer_Data'].isna() == True]


# In[46]:


# the length of the rest should match the expected number of acquistions 
print(len(us_df[us_df['Transducer'].isna() == False]))


# In[47]:


# the length of the rest should match the expected number of acquistions 
print(len(us_df[us_df['Transducer_Data'].isna() == False]))


# In[48]:


# now, we need to assing every batch of 50 ultrasound frames (1 second) to the corresponding batch of EMG data 
# combined_df = emg_df.copy()

# cnt_wulpus_batch = 0


# for idx_wulpus_cnt, idx_wulpus_biogap in enumerate(idx_wulpus):
#     #if idx_wulpus_biogap!=idx_wulpus[-1]:

#     if idx_wulpus_biogap!=idx_wulpus[-1]:
#         print(f'Batch number:{cnt_wulpus_batch}')
#         start_wulpus_batch = cnt_wulpus_batch * 50
#         stop_wulpus_batch = start_wulpus_batch + 49
#         print(f'Considering US frames from:{start_wulpus_batch} to {stop_wulpus_batch}')
#         us_df_curr = us_df.loc[start_wulpus_batch:stop_wulpus_batch]
#         print(f"Lost:{len(us_df_curr[us_df_curr['Transducer'].isna()==True])} US frames for this batch")
        
#         biogap_idx_start = idx_wulpus_biogap
#         biogap_idx_stop = idx_wulpus[idx_wulpus_cnt+1] -1
#         print(f'Num EMG samples in between: {biogap_idx_stop - biogap_idx_start}')

#         freq_scaling = 500 / 50
#         new_wps_idx = np.arange(biogap_idx_start, biogap_idx_stop, freq_scaling)
#         us_df_curr = us_df_curr.set_index(new_wps_idx)

#         combined_df.loc[new_wps_idx, 'Transducer'] = us_df_curr['Transducer']
#         combined_df.loc[new_wps_idx, 'Transducer_Data'] = us_df_curr['Transducer_Data']
#         cnt_wulpus_batch+=1
        
        
#     #else:
#         # enter here for the last (max) 50 samples acquired
#     #    print('last batch')
#     print('---')


# In[49]:


# now, we need to assing every batch of 50 ultrasound frames (1 second) to the corresponding batch of EMG data 

freq_scaling = 500 / 50
counter_every_50_frames = 49                    # 
combined_df = emg_df.copy()

cnt_wulpus_batch = 0

wulpus_bloks = []
for idx_wulpus_cnt, idx_wulpus_biogap in enumerate(idx_wulpus):
    #if idx_wulpus_biogap!=idx_wulpus[-1]:

    
    print(f'Batch number:{cnt_wulpus_batch}')
    start_wulpus_batch = cnt_wulpus_batch * 50
    if idx_wulpus_biogap!=idx_wulpus[-1]:
        stop_wulpus_batch = start_wulpus_batch + 49
    else:
        stop_wulpus_batch = acq_num_arr[-1]
    print(f'Considering US frames from:{start_wulpus_batch} to {stop_wulpus_batch}')
    us_df_curr = us_df.loc[start_wulpus_batch:stop_wulpus_batch]
    print(f'Current US df has len: {len(us_df_curr)}')
    print(f"Lost:{len(us_df_curr[us_df_curr['Transducer_Data'].isna()==True])} US frames for this batch")
    
    # idx wulpus biogap corresponds to the 50th - 100th .... Ultrasound frame
    biogap_idx_start = idx_wulpus_biogap - counter_every_50_frames * freq_scaling                
    print(f'Biogap idx starts at: {biogap_idx_start}, stops at: {idx_wulpus_biogap}')
    print(f'Start - stop difference : {idx_wulpus_biogap - biogap_idx_start}')
    
    new_wps_idx = np.linspace(biogap_idx_start, idx_wulpus_biogap, num = len(us_df_curr), dtype=int)
    wulpus_bloks.extend([new_wps_idx[0], new_wps_idx[-1]])
    print(new_wps_idx)
    
    us_curr_acq_num_arr = us_df_curr.index
    print(us_curr_acq_num_arr)
    us_df_curr = us_df_curr.set_index(new_wps_idx)

    combined_df.loc[new_wps_idx, 'Transducer'] = us_df_curr['Transducer']
    combined_df.loc[new_wps_idx, 'Transducer_Data'] = us_df_curr['Transducer_Data']
    combined_df.loc[new_wps_idx, 'US acq_num_array'] =us_curr_acq_num_arr
    #print(combined_df.loc[new_wps_idx, 'US acq_num_array'])
    cnt_wulpus_batch+=1
        
        
    #else:
        # enter here for the last (max) 50 samples acquired
    #    print('last batch')
    print('---')

# assign all the remainin samples
# start_wulpus_batch = cnt_wulpus_batch * 50
# stop_wulpus_batch = acq_num_arr[-1]
# us_df_curr = us_df.loc[start_wulpus_batch:]
# us_curr_acq_num_arr = us_df_curr.index
# print(f'Considering US frames from:{start_wulpus_batch} to {stop_wulpus_batch}')
# remaining_samples = stop_wulpus_batch-start_wulpus_batch + 1
# print(f'Remianing:{remaining_samples} samples')

# biogap_idx_start = new_wps_idx[-1] + freq_scaling
# new_wps_idx = np.linspace(biogap_idx_start, biogap_idx_start + remaining_samples*freq_scaling, remaining_samples, dtype=int)
# print(new_wps_idx)
# us_df_curr = us_df_curr.set_index(new_wps_idx)

# combined_df.loc[new_wps_idx, 'Transducer'] = us_df_curr['Transducer']
# combined_df.loc[new_wps_idx, 'Transducer_Data'] = us_df_curr['Transducer_Data']
# combined_df.loc[new_wps_idx, 'US acq_num_array'] =us_curr_acq_num_arr
# wulpus_bloks.extend([new_wps_idx[0], new_wps_idx[-1]])


# In[50]:


plt.figure()
plt.plot(emg_df['Trigger_Wulpus'])
plt.plot(wulpus_bloks, emg_df['Trigger_Wulpus'].loc[wulpus_bloks], marker='o', linestyle='none')
plt.show()


# In[ ]:





# In[51]:


combined_df = combined_df.loc[idx_wulpus[0] - 490: combined_df[combined_df['Transducer_Data'].isna() == False].index[-1], :]


# In[52]:


print(f'Acquired: {acquired_samples} for Wulpus')


# In[53]:


# total lenght of acquisitions of Ultrasound Data
print(f'Acquired ultrasound for: {acq_num_arr[-1] * 20} ms')
print(f'This corresponds to: {int(acq_num_arr[-1] * 20 / 2)} EMG samples')


# In[54]:


combined_df[combined_df['Transducer_Data'].isna() == False]


# In[55]:


index_not_nan = combined_df[combined_df['Transducer_Data'].isna()==False].index
len(index_not_nan)


# In[56]:


from scipy import signal as ss
# Filter Ultrasound Data
f_low = 0.55 * US_PRR
f_high = 1.45 * US_PRR

b, a = ss.butter(4, [f_low / (US_FS / 2), f_high / (US_FS / 2)], btype='bandpass')
index_not_nan = combined_df[combined_df['Transducer_Data'].isna()==False].index
data_filtered = ss.filtfilt(b, a, np.vstack(combined_df.loc[index_not_nan, 'Transducer_Data']))

# Hilbert Envelope Extraction
data_env = np.abs(hilbert(data_filtered, axis=1))

# Create a copy of the DataFrame for processed data
combined_df_proc = combined_df.copy()

# Assign filtered and envelope data to the new DataFrame
combined_df_proc.loc[index_not_nan, 'Transducer_Data_Filt'] = pd.Series(list(data_filtered), index=index_not_nan)
combined_df_proc.loc[index_not_nan, 'Transducer_Data_Hilb'] = pd.Series(list(data_env), index=index_not_nan)


# In[57]:


combined_df_proc[combined_df_proc['Transducer_Data_Filt'].isna() == False]


# In[58]:


np.unique((np.diff(combined_df_proc[combined_df_proc['Transducer']==0].index)))


# In[82]:


def plot_sync_emg_us(combined_df):

     # plotting some data as example
    fig, axs = plt.subplots(3, 1, sharex=True)
    plt.subplots_adjust(hspace=0.1)

    # Overall x-axis range (based on the entire combined_df)
    #x_min, x_max = combined_df['Timestamp_reconstructed'].iloc[0], combined_df['Timestamp_reconstructed'].iloc[-1]
    x_min, x_max = combined_df.index[0], combined_df.index[-1]
    ch_to_plot = [1]
    cnt_fig=0
    
    #axs[cnt_fig].plot(timestamps_emg, combined_df[f'Ch{cnt_fig+1}'].values)
    axs[cnt_fig].plot(combined_df.index, combined_df[f'Ch{ch_to_plot[cnt_fig]}'].values)
    
    axs[cnt_fig].set_xlim(x_min, x_max)
    axs[cnt_fig].set_title(f'EMG - Ch{ch_to_plot[cnt_fig]}')
    axs[cnt_fig].set_ylabel('Amplitude [uV]')

    cnt_fig +=1

    # Loop over the transducers
    imaging_depths = compute_us_imaging_depths()
    #print(np.where(np.isnan(np.vstack(combined_df['Transducer_Data_Hilb'])).all(axis=1))[0])

    
    # Filter the data for the current transducer
    tx = combined_df[combined_df['Transducer'] == 0]
    tx_start = tx.index[0]
    tx_stop = tx.index[-1]
    #tx = combined_df.loc[tx_start:tx_stop:80]

    # Identify rows with NaN 

    nan_rows = nan_rows = tx[tx['Transducer_Data_Hilb'].isna() == True]
    #print(nan_rows)
    
    print(f'Got NaNs for current transducer:{len(nan_rows)}')

    # Create a pandas Series with arrays of 400 NaNs for the affected rows
    nan_arrays = pd.Series([np.full(400, np.nan) for _ in range(len(nan_rows))], index=nan_rows.index)
    #zero_arrays = pd.Series([np.full(400, 0) for _ in range(len(nan_rows))], index=nan_rows.index)
    # Assign the new Series to the 'Transducer_Data_Hilb' column
    tx.loc[nan_rows.index, 'Transducer_Data_Hilb'] = nan_arrays

    # Extract data for plotting
    us_array = np.vstack(tx['Transducer_Data_Hilb']).T
    #print(np.shape(np.isnan(us_array)))
    # Configure colormap to handle NaNs
    cmap = plt.cm.viridis
    #cmap.set_bad(color="red")  # Set NaNs to red
    # Define extent
    extent = [
        tx_start,
        tx_stop,
        imaging_depths[-1],
        imaging_depths[0],
    ]
    
    print(extent[0], extent[1])
    # Plot the transducer data
    axs[cnt_fig].imshow(
        us_array,
        extent=extent,
        aspect="auto",
        #cmap='grey',
        origin="upper",
        interpolation = "none", 
        #vmin=1, 
        
    )
    axs[cnt_fig].set_xlim(x_min, x_max)
    axs[cnt_fig].set_ylabel("Depth [mm]")
        
    #axs[cnt_fig].plot(combined_df.index,combined_df['Trigger_gui'] )
    cnt_fig+=1
    axs[cnt_fig].plot(combined_df.index, combined_df['Trigger_Wulpus'].values)
    axs[cnt_fig].set_xlabel('Time [ms]')
    axs[cnt_fig].set_xlim(x_min, x_max)
    #plt.tight_layout()
    plt.show()





# In[83]:


plot_sync_emg_us(combined_df_proc)


# In[88]:


#plot_sync_emg_us(combined_df_proc.loc[:150000])
plot_sync_emg_us(combined_df_proc.loc[emg_idx_effect[-1]-20:])


# In[78]:





# In[63]:


plot_sync_emg_us(combined_df_proc.loc[:150000])


# In[65]:


plot_sync_emg_us(combined_df_proc.loc[emg_idx_effect[-4]-20 : emg_idx_effect[-3]+20])         #until 192400 works, then breaks OKAY


# In[77]:


plot_sync_emg_us(combined_df_proc.loc[emg_idx_effect[5]-20 : emg_idx_effect[6]+40])         #until 192400 works, then breaks OKAY


# In[76]:


plot_sync_emg_us(combined_df_proc)


# In[68]:


plot_sync_emg_us(combined_df_proc)


# In[69]:


plot_sync_emg_us(combined_df_proc.loc[170000:200000])


# In[70]:


(combined_df_proc['US acq_num_array'].iloc[-1] / 50) * 1000   #ms 


# In[71]:


emg_idx_effect


# In[72]:


plt.figure()
plt.plot(combined_df_proc.loc[188388]['Transducer_Data'])


