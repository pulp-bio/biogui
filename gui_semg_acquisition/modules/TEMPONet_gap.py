import torch.nn as nn
import torch.nn.functional as F
from torch import movedim
from math import ceil

class TEMPONet_gap(nn.Module):
    """
    TEMPONet architecture:
    Three repeated instances of TemporalConvBlock and ConvBlock organized as follows:
    - TemporalConvBlock
    - ConvBlock
    Two instances of Regressor followed by a final Linear layer with a single neuron.
    """
    def __init__(self, dataset_name='PPG_Dalia', dataset_args={}):
        super(TEMPONet_gap, self).__init__()

        self.dil = [
                2, 2, 1,
                4, 4, 1,
                8, 8, 1
                ]
        self.rf = [
                5, 5, 5,
                9, 9, 5,
                17, 17, 5
                ]
        self.ch = [
            8, 8, 8,
            16, 16, 16,
            32, 32, 32,
            64, 1
        ]
        # 1st instance of two TempConvBlocks and ConvBlock
        k_tcb00 = [ceil(self.rf[0]/self.dil[0]),1]
        self.tcb00 = TempConvBlock(
                ch_in = 2,
                ch_out = self.ch[0],
                k_size = k_tcb00,
                dil = [self.dil[0],1],
                pad = [((k_tcb00[0]-1)*self.dil[0]+1)//2,0]
                )
        k_tcb01 = [ceil(self.rf[1]/self.dil[1]),1]
        self.tcb01 = TempConvBlock(
                ch_in = self.ch[0],
                ch_out = self.ch[1],
                k_size = k_tcb01,
                dil = [self.dil[1],1],
                pad = [((k_tcb01[0]-1)*self.dil[1]+1)//2,0]
                )
        k_cb0 = [ceil(self.rf[2]/self.dil[2]),1]
        self.cb0 = ConvBlock(
                ch_in = self.ch[1],
                ch_out = self.ch[2],
                k_size = k_cb0,
                strd = [4,1],
                pad = [((k_cb0[0]-1)*self.dil[2]+1)//2,0],
                dilation = [self.dil[2],1],
                strd_avg  = [2,1]
                )

        # 2nd instance of two TempConvBlocks and ConvBlock
        k_tcb10 = [ceil(self.rf[3]/self.dil[3]),1]
        self.tcb10 = TempConvBlock(
                ch_in = self.ch[2],
                ch_out = self.ch[3],
                k_size = k_tcb10,
                dil = [self.dil[3],1],
                pad = [((k_tcb10[0]-1)*self.dil[3]+1)//2,0]
                )
        k_tcb11 = [ceil(self.rf[4]/self.dil[4]),1]
        self.tcb11 = TempConvBlock(
                ch_in = self.ch[3],
                ch_out = self.ch[4],
                k_size = k_tcb11,
                dil = [self.dil[4],1],
                pad = [((k_tcb11[0]-1)*self.dil[4]+1)//2,0]
                )
        k_cb1 = [ceil(self.rf[5]/self.dil[5]),1]
        self.cb1 = ConvBlock(
                ch_in = self.ch[4],
                ch_out = self.ch[5],
                k_size = k_cb1,
                strd = [4,1],
                pad = [((k_cb1[0]-1)*self.dil[5]+1)//2,0],
                strd_avg  = [2,1]
                )

        # 3td instance of TempConvBlock and ConvBlock
        k_tcb20 = [ceil(self.rf[6]/self.dil[6]),1]
        self.tcb20 = TempConvBlock(
                ch_in = self.ch[5],
                ch_out = self.ch[6],
                k_size = k_tcb20,
                dil = [self.dil[6],1],
                pad = [((k_tcb20[0]-1)*self.dil[6]+1)//2,0]
                )
        k_tcb21 = [ceil(self.rf[7]/self.dil[7]),1]
        self.tcb21 = TempConvBlock(
                ch_in = self.ch[6],
                ch_out = self.ch[7],
                k_size = k_tcb21,
                dil = [self.dil[7],1],
                pad = [((k_tcb21[0]-1)*self.dil[7]+1)//2,0]
                )
        # self.padding = nn.ConstantPad2d((0,0,1,1), 0)
        k_cb2 = [ceil(self.rf[8]/self.dil[8]),1]
        self.cb2 = ConvBlock(
                ch_in = self.ch[7],
                ch_out = self.ch[8],
                k_size = k_cb2,
                strd = [4,1],
                pad = [((k_cb2[0]-1)*self.dil[8]+1)//2, 0],
                strd_avg  = [2,1]
                )
        # # 1st instance of regressor
        self.fc0 = FC(
                ft_in = self.ch[8] * 5,
                ft_out = self.ch[9]
        )

        # 2nd instance of FC
        self.fc1 = nn.Linear(self.ch[9], self.ch[10])
        # self.out_neuron = nn.Linear(
        #         in_features = self.ch[10],
        #         out_features = 1
        #         )

    def forward(self, x):
        x = self.cb0(
                self.tcb01(
                    self.tcb00(
                        x
                        )
                    )
                )
        x = self.cb1(
                self.tcb11(
                    self.tcb10(
                        x
                        )
                    )
                )
        # x = self.cb2(
        #         self.tcb21(
        #             self.tcb20(
        #                 x
        #                 )
        #             )
        #         )
        x = self.tcb21(
        self.tcb20(
                x
                )
        )
        # x = self.padding(x)
        x = self.cb2(x)

        x = x.flatten(1)
        x = self.fc0(
                x
        )
        x = self.fc1(
                x
        )

        return x

class TempConvBlock(nn.Module):
    """
    Temporal Convolutional Block composed of one temporal convolutional layers.
    The block is composed of :
    - Conv1d layer
    - Chomp1d layer
    - ReLU layer
    - BatchNorm1d layer

    :param ch_in: Number of input channels
    :param ch_out: Number of output channels
    :param k_size: Kernel size
    :param dil: Amount of dilation
    :param pad: Amount of padding
    """
    def __init__(self, ch_in, ch_out, k_size, dil, pad):
        super(TempConvBlock, self).__init__()

        self.tcn0 = nn.Conv2d(
                in_channels = ch_in,
                out_channels = ch_out,
                kernel_size = k_size,
                dilation = dil,
                padding = pad
                )
        self.bn0 = nn.BatchNorm2d(
                num_features = ch_out
                )

        self.relu0 = nn.ReLU()


    def forward(self, x):
        x = self.relu0(
                self.bn0(
                        self.tcn0(x)
                )
        )
        return x

class ConvBlock(nn.Module):
    """
    Convolutional Block composed of:
    - Conv1d layer
    - AvgPool1d layer
    - ReLU layer
    - BatchNorm1d layer

    :param ch_in: Number of input channels
    :param ch_out: Number of output channels
    :param k_size: Kernel size
    :param strd: Amount of stride
    :param pad: Amount of padding
    """
    def __init__(self, ch_in, ch_out, k_size, strd, pad, strd_avg, dilation=1):
        super(ConvBlock, self).__init__()

        self.conv0 = nn.Conv2d(
                in_channels = ch_in,
                out_channels = ch_out,
                kernel_size = k_size,
                stride = strd,
                dilation = dilation,
                padding = pad
                )
        self.pool0 = nn.AvgPool2d(
                kernel_size = [2,1],
                stride = strd_avg,
                padding = 0
                )
        self.bn0 = nn.BatchNorm2d(ch_out)
        self.relu0 = nn.ReLU()


    def forward(self, x):
        x = self.relu0(
                self.bn0(
                        self.pool0(
                                self.conv0(
                                        x
                                )

                        )
                )
        )

        return x

class FC(nn.Module):
    """
    Regressor block  composed of :
    - Linear layer
    - ReLU layer
    - BatchNorm1d layer

    :param ft_in: Number of input channels
    :param ft_out: Number of output channels
    """
    def __init__(self, ft_in, ft_out):
        super(FC, self).__init__()
        self.ft_in = ft_in
        self.ft_out = ft_out

        self.fc0 = nn.Linear(
                in_features = ft_in,
                out_features = ft_out
            )
        self.bn0 = nn.BatchNorm2d(
                num_features = ft_out
            )

        self.relu0 = nn.ReLU()
        self.drop0 = nn.Dropout()


    def forward(self, x):
        x = self.fc0(x)
        x = x.view(*x.size(),1,1)
        x = self.drop0(
                self.relu0(
                        self.bn0(

                                x

                        )
                )
        )
        x = x.squeeze()
        return x
class Chomp1d(nn.Module):
    """
    Module that perform a chomping operation on the input tensor.
    It is used to chomp the amount of zero-padding added on the right of the input tensor, this operation is necessary to compute causal convolutions.
    :param chomp_size: amount of padding 0s to be removed
    """
    def __init__(self, chomp_size):
        super(Chomp1d, self).__init__()
        self.chomp_size = chomp_size

    def forward(self, x):
        return x[:, :, :-self.chomp_size].contiguous()
