import torch
import torch.nn as nn

def First_dense_block(n, int_c, g, a, dropout):
    return nn.Sequential(
                nn.BatchNorm2d(int_c+(n-1)*g),
                nn.ReLU(),
                nn.Conv2d(int_c +(n-1)*g, g*a, 1, 1),
                nn.Dropout(p=dropout),
                
                nn.BatchNorm2d(g*a),
                nn.ReLU(),
                nn.Conv2d(g*a, g, 3, 1, 1),
                nn.Dropout(p=dropout)
            )

def Second_dense_block(n, int_c, g, a, dropout):
    return nn.Sequential(
                nn.BatchNorm2d(int(int_c/2)+(n+2)*g),
                nn.ReLU(),
                nn.Conv2d(int(int_c/2)+(n+2)*g, g*a, 1, 1),
                nn.Dropout(p=dropout),
                
                nn.BatchNorm2d(g*a),
                nn.ReLU(),
                nn.Conv2d(g*a, g, 3, 1, 1),
                nn.Dropout(p=dropout)
            )
                    
class DDCNN(nn.Module):
    def __init__(self, num_bands, num_classes, dropout=0.1):
        super().__init__()
        self.num_bands = num_bands
        self.num_classes = num_classes
        self.dropout=dropout
        self.modelType = "CLS"
    
        self.int_c = 16 
        self.g = 32
        self.a = 4

        #C0
        self.conv1 = nn.Conv2d(num_bands, self.int_c, 3, 1)  

        #D1
        self.B1_1 = First_dense_block(1, self.int_c, self.g, self.a, self.dropout)
        self.B1_2 = First_dense_block(2, self.int_c, self.g, self.a, self.dropout)
        self.B1_3 = First_dense_block(3, self.int_c, self.g, self.a, self.dropout)
        self.B1_4 = First_dense_block(4, self.int_c, self.g, self.a, self.dropout)
        self.B1_5 = First_dense_block(5, self.int_c, self.g, self.a, self.dropout)
        self.B1_6 = First_dense_block(6, self.int_c, self.g, self.a, self.dropout)
        
        #T2
        self.T2 = nn.Sequential(
                        nn.BatchNorm2d(self.int_c+6*self.g),
                        nn.ReLU(),
                        nn.Conv2d(self.int_c+6*self.g, int(self.int_c/2)+3*self.g, 1, 1),
                        nn.Dropout(p=self.dropout),
                    )

        #D3
        self.B3_1 = Second_dense_block(1, self.int_c, self.g, self.a, self.dropout)
        self.B3_2 = Second_dense_block(2, self.int_c, self.g, self.a, self.dropout)
        self.B3_3 = Second_dense_block(3, self.int_c, self.g, self.a, self.dropout)
        self.B3_4 = Second_dense_block(4, self.int_c, self.g, self.a, self.dropout)
        self.B3_5 = Second_dense_block(5, self.int_c, self.g, self.a, self.dropout)
        self.B3_6 = Second_dense_block(6, self.int_c, self.g, self.a, self.dropout)
        self.B3_7 = Second_dense_block(7, self.int_c, self.g, self.a, self.dropout)
        self.B3_8 = Second_dense_block(8, self.int_c, self.g, self.a, self.dropout)
        self.B3_9 = Second_dense_block(9, self.int_c, self.g, self.a, self.dropout)
        self.B3_10 = Second_dense_block(10, self.int_c, self.g, self.a, self.dropout)
        self.B3_11 = Second_dense_block(11, self.int_c, self.g, self.a, self.dropout)
        self.B3_12 = Second_dense_block(12, self.int_c, self.g, self.a, self.dropout)
        self.B3_13 = Second_dense_block(13, self.int_c, self.g, self.a, self.dropout)
        self.B3_14 = Second_dense_block(14, self.int_c, self.g, self.a, self.dropout)
        self.B3_15 = Second_dense_block(15, self.int_c, self.g, self.a, self.dropout)
        self.B3_16 = Second_dense_block(16, self.int_c, self.g, self.a, self.dropout)
        
        #Final
        self.Final = nn.Sequential(
                            nn.BatchNorm2d(int(self.int_c/2)+19*self.g),
                            nn.ReLU(),
                            nn.AdaptiveAvgPool2d(1)
                    )


        self.features_size = int(self.int_c/2)+19*self.g
        self.fc1 = nn.Linear(self.features_size, num_classes)

    def forward(self, img):
        img = img/4095.0
        x = self.conv1(img)

        #D2
        x1 = self.B1_1(x)
        fx1 = torch.cat([x, x1], 1)

        x2 = self.B1_2(fx1)
        fx2= torch.cat([x, x1, x2], 1)

        x3 = self.B1_3(fx2)
        fx3= torch.cat([x, x1, x2, x3], 1)

        x4 = self.B1_4(fx3)
        fx4= torch.cat([x, x1, x2, x3, x4], 1)

        x5 = self.B1_5(fx4)
        fx5= torch.cat([x, x1, x2, x3, x4, x5], 1)

        x6 = self.B1_6(fx5)
        fx6= torch.cat([x, x1, x2, x3, x4, x5, x6], 1)

        #T2
        T = self.T2(fx6)
        T = nn.functional.avg_pool2d(T, 2, 2)

        #D3
        x1 = self.B3_1(T)
        fx1 = torch.cat([T, x1], 1)

        x2 = self.B3_2(fx1)
        fx2 = torch.cat([T, x1, x2], 1)

        x3 = self.B3_3(fx2)
        fx3 = torch.cat([T, x1, x2, x3], 1)

        x4 = self.B3_4(fx3)
        fx4 = torch.cat([T, x1, x2, x3, x4], 1)

        x5 = self.B3_5(fx4)
        fx5 = torch.cat([T, x1, x2, x3, x4, x5], 1)

        x6 = self.B3_6(fx5)
        fx6 = torch.cat([T, x1, x2, x3, x4, x5, x6], 1)

        x7 = self.B3_7(fx6)
        fx7 = torch.cat([T, x1, x2, x3, x4, x5 ,x6 ,x7], 1)

        x8 = self.B3_8(fx7)
        fx8 = torch.cat([T, x1, x2, x3, x4, x5, x6, x7, x8], 1)

        x9 = self.B3_9(fx8)
        fx9 = torch.cat([T, x1, x2, x3, x4, x5, x6, x7, x8, x9], 1)

        x10 = self.B3_10(fx9)
        fx10 = torch.cat([T, x1, x2, x3, x4, x5, x6, x7, x8, x9, x10], 1)

        x11 = self.B3_11(fx10)
        fx11 = torch.cat([T, x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11], 1)

        x12 = self.B3_12(fx11)
        fx12 = torch.cat([T, x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12], 1)

        x13 = self.B3_13(fx12)
        fx13 = torch.cat([T, x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13], 1)

        x14 = self.B3_14(fx13)
        fx14 = torch.cat([T, x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14], 1)

        x15 = self.B3_15(fx14)
        fx15 = torch.cat([T, x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14, x15], 1)

        x16 = self.B3_16(fx15)
        fx16 = torch.cat([T, x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14, x15, x16], 1)

        Final = self.Final(fx16)
        fc = Final.view(-1, self.features_size)
        fc = self.fc1(fc)
        return fc