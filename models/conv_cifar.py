from __future__ import print_function
import torch
import torch.utils.data
import torch.nn as nn
from models.AbsModel import AbsModel
from torch.nn.utils import weight_norm

class VAE(AbsModel):
    def __init__(self, args):
        super(VAE, self).__init__(args)

    def create_model(self, args, train_data_size=None):
        class block(nn.Module):
            def __init__(self, input_size, output_size, stride=1, kernel=3, padding=1):
                super(block, self).__init__()
                self.normalization = nn.BatchNorm2d(input_size)
                self.conv1 = weight_norm(nn.Conv2d(input_size, output_size, kernel_size=kernel,
                                                   stride=stride, padding=padding,
                                       bias=True))
                self.conv2 = weight_norm(
                    nn.Conv2d(output_size, output_size, kernel_size=kernel, stride=stride, padding=padding,
                              bias=True))
                self.activation = torch.nn.ELU()
                self.f = torch.nn.Sequential(self.activation, self.conv1, self.activation, self.conv2)

            def forward(self, x):
                return x + self.f(x)

        self.train_data_size = train_data_size
        self.cs = 100
        self.bottleneck = self.args.bottleneck

        self.q_z_layers = nn.Sequential(
            nn.ELU(),
            weight_norm(nn.Conv2d(in_channels=self.args.input_size[0], out_channels=self.cs, kernel_size=3, stride=2, padding=1)),
            *[block(input_size=self.cs, output_size=self.cs, stride=1, kernel=3, padding=1) for _ in range(self.args.rs_blocks)],
        )

        self.q_z_mean = nn.Sequential(
            nn.ELU(),
            weight_norm(nn.Conv2d(in_channels=self.cs, out_channels=self.bottleneck, kernel_size=3, stride=1, padding=1)))

        self.q_z_logvar = nn.Sequential(
            nn.ELU(),
            weight_norm(nn.Conv2d(in_channels=self.cs, out_channels=self.bottleneck, kernel_size=3, stride=1, padding=1)))

        self.p_x_layers = nn.Sequential(
            nn.Upsample(scale_factor=2),
            nn.ELU(),
            weight_norm(nn.Conv2d(in_channels=self.bottleneck, out_channels=self.cs, kernel_size=3, stride=1, padding=1)),
            *[block(input_size=self.cs, output_size=self.cs, stride=1, kernel=3, padding=1) for _ in range(self.args.rs_blocks)],
        )

        if self.args.input_type == 'binary':
            self.p_x_mean = nn.Sequential(nn.Conv2d(in_channels=self.cs,
                                                    out_channels=self.args.input_size[0],
                                                    kernel_size=3,
                                                    stride=1, padding=1), nn.Sigmoid())
        elif self.args.input_type == 'gray' or self.args.input_type == 'continuous':
            self.p_x_mean = nn.Sequential(nn.ELU(),
                                          weight_norm(nn.Conv2d(in_channels=self.cs,
                                                                out_channels=self.args.input_size[0],
                                                                kernel_size=3, stride=1, padding=1)))

