import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from torch.utils.data import DataLoader, TensorDataset

from .seeds import *


def create_dataloader(
    df,
    us_window_size=397,
    batch_size=None,
    shuffle=False,
    return_df=False,
    drop_last=True,
    ):
    """
    Function to return Dataloader for Ultrasound data

    df : dataframe containing EMG - US data (or CAE features) - labels

    ================ US parameters =================================
    num_us_channels : number of Ultrasound Channels - Transducers
    us_window_size : size of Ultrasound Data
    ================ General parameters =============================
    batch_size = batch size to consider
    shuffle: True if want to shuffle data, else False

    return_df: True if want to return the dataframe containing the data, else False
    drop_last: True if want to drop the last batch if it is smaller than batch size, else False
    """
    us_columns = df.columns[df.columns.str.contains("ultrasound")]
    num_rows = df.shape[0]
    num_us_channels = len(us_columns)

    X_us_tensor = torch.empty((num_rows, num_us_channels, us_window_size))

    # loop through each row of EMG data and appending eventual Nan Values
    for i, idx in enumerate(df.index):
        X_us_tensor[i, :, :] = torch.tensor(np.array(df.loc[idx, us_columns].to_list()))

    ####################################################################################################################################
    #################################### Label tensor creation #########################################################################
    # Now consider the labels
    labels_to_select = df.columns[df.columns.str.contains("label")]
    assert len(labels_to_select) == 1, "CrossEntropyLoss needs a single label column."

    label_col = labels_to_select[0]
    y_np = df[label_col].astype(int).to_numpy()  # ensure numeric

    # IMPORTANT: make sure we start from 0
    if np.min(y_np) != 0:
        y_np = y_np - 1  # map 1->0, 2->1

    y_tensor = torch.tensor(y_np, dtype=torch.long)  # shape: (num_rows,)

    #################################### DataLoader instance ###########################################################################
    dataset_us = TensorDataset(X_us_tensor, y_tensor)
    # drop_last set to True to prevent small batches
    dataloader_us = DataLoader(
        dataset_us,
        batch_size=32,
        shuffle=shuffle,
        drop_last=drop_last,  # drop_last set to True to prevent small batches
    )

    if return_df and not drop_last:
        return dataloader_us, df

    if (
        return_df and drop_last and not shuffle
    ):  # we match these conditions only in yest set
        # make sure that df has the same len of the dataloader (drop_last = true will remove )
        print(f"df has shape:{df.shape}")
        # print(f'dataloader us has shape: {len(dataloader_us.dataset)}')
        effective_len = (df.shape[0] // batch_size) * batch_size
        df = df.iloc[:effective_len, :]
        print(f"df adjusted has shape:{df.shape}")
        return dataloader_us, df
    else:
        return dataloader_us


# def train_loop(model, trainloader, valoader, num_epochs, save_path=None, device="cpu"):
#     criterion = nn.CrossEntropyLoss()
#     optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

#     train_losses = []
#     val_losses = []
#     best_val_loss = float("inf")
#     best_state = None

#     patience = 0
#     early_stop_patience = 5

#     model.to(device)

#     for epoch in range(num_epochs):
#         # -------- Train --------
#         model.train()
#         running_loss_train = 0.0
#         train_batches = 0

#         for x, y in trainloader:
#             x = x.to(device)
#             y = y.to(device)

#             optimizer.zero_grad()
#             outputs = model(x)
#             loss = criterion(outputs, y)
#             loss.backward()
#             optimizer.step()

#             running_loss_train += loss.item()
#             train_batches += 1

#         avg_train_loss = running_loss_train / train_batches

#         # -------- Validation --------
#         model.eval()
#         running_loss_val = 0.0
#         val_batches = 0

#         with torch.no_grad():
#             for x, y in valoader:
#                 x = x.to(device)
#                 y = y.to(device)

#                 outputs = model(x)
#                 loss = criterion(outputs, y)

#                 running_loss_val += loss.item()
#                 val_batches += 1

#         avg_val_loss = running_loss_val / val_batches

#         # Early stopping bookkeeping
#         if avg_val_loss < best_val_loss:
#             best_val_loss = avg_val_loss
#             best_state = {
#                 "model_state_dict": model.state_dict(),
#                 "optimizer_state_dict": optimizer.state_dict(),
#                 "epoch": epoch,
#             }
#             patience = 0
#         else:
#             patience += 1
#             print(f"Consecutive epochs without improvement: {patience}")
#             if patience >= early_stop_patience:
#                 print("Hit early stopping.")
#                 break

#         print(
#             f"{epoch} TRAIN loss: {avg_train_loss:.3f} | VAL loss: {avg_val_loss:.3f}"
#         )
#         train_losses.append(avg_train_loss)
#         val_losses.append(avg_val_loss)

#     # Save best model and loss history
#     if save_path is not None and best_state is not None:
#         best_state.update(
#             {
#                 "train_loss": train_losses,
#                 "val_loss": val_losses,
#                 "best_val_loss": best_val_loss,
#             }
#         )
#         torch.save(best_state, save_path)

#     # Optionally restore best model weights before returning
#     if best_state is not None:
#         model.load_state_dict(best_state["model_state_dict"])

#     return model


# def test_model(model, testloader, device="cpu"):
#     model.eval()

#     all_targets = []
#     all_preds = []
#     all_logits = []

#     with torch.no_grad():
#         for inputs, targets in testloader:
#             inputs = inputs.to(device)
#             targets = targets.to(device)

#             outputs = model(inputs)  # logits: (batch_size, num_classes)
#             preds = outputs.argmax(dim=1)  # predicted class index

#             all_targets.append(targets.cpu())
#             all_preds.append(preds.cpu())
#             all_logits.append(outputs.cpu())

#     # Concatenate batches
#     y_true = torch.cat(all_targets).numpy()
#     y_pred = torch.cat(all_preds).numpy()
#     logits = torch.cat(all_logits).numpy()

#     # ===== Metrics summary =====
#     acc = accuracy_score(y_true, y_pred)

#     precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
#         y_true, y_pred, average="macro", zero_division=0
#     )
#     cm = confusion_matrix(y_true, y_pred)

#     metrics = {
#         "accuracy": acc,
#         "precision_macro": precision_macro,
#         "recall_macro": recall_macro,
#         "f1_macro": f1_macro,
#         "confusion_matrix": cm,
#     }

#     # Pretty print a short summary
#     print("=== Test Metrics ===")
#     print(f"Accuracy        : {acc:.4f}")
#     print(f"Precision (macro): {precision_macro:.4f}")
#     print(f"Recall (macro)   : {recall_macro:.4f}")
#     print(f"F1-score (macro) : {f1_macro:.4f}")
#     print("Confusion matrix:")
#     # print(cm)

#     return metrics, y_true, y_pred, logits
