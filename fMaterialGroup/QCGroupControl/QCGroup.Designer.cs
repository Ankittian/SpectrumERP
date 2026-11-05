namespace QCGroupdll
{
    partial class QCGroup
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Component Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify 
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.ulblQCGroup = new Infragistics.Win.Misc.UltraLabel();
            this.ugdQCGroup = new Infragistics.Win.UltraWinGrid.UltraGrid();
            this.ugbQCGroup = new Infragistics.Win.Misc.UltraGroupBox();
            this.ubtnCancel = new Infragistics.Win.Misc.UltraButton();
            this.ubtnOK = new Infragistics.Win.Misc.UltraButton();
            this.ucmbQCGroup = new Infragistics.Win.UltraWinGrid.UltraCombo();
            ((System.ComponentModel.ISupportInitialize)(this.ugdQCGroup)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.ugbQCGroup)).BeginInit();
            this.ugbQCGroup.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.ucmbQCGroup)).BeginInit();
            this.SuspendLayout();
            // 
            // ulblQCGroup
            // 
            this.ulblQCGroup.AutoSize = true;
            this.ulblQCGroup.Location = new System.Drawing.Point(7, 9);
            this.ulblQCGroup.Name = "ulblQCGroup";
            this.ulblQCGroup.Size = new System.Drawing.Size(97, 16);
            this.ulblQCGroup.TabIndex = 0;
            this.ulblQCGroup.Text = "QC Group &Name";
            // 
            // ugdQCGroup
            // 
            this.ugdQCGroup.Anchor = ((System.Windows.Forms.AnchorStyles)((((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom)
                        | System.Windows.Forms.AnchorStyles.Left)
                        | System.Windows.Forms.AnchorStyles.Right)));
            this.ugdQCGroup.Location = new System.Drawing.Point(6, 33);
            this.ugdQCGroup.Name = "ugdQCGroup";
            this.ugdQCGroup.Size = new System.Drawing.Size(763, 191);
            this.ugdQCGroup.TabIndex = 2;
            this.ugdQCGroup.Text = "ultraGrid1";
            this.ugdQCGroup.AfterCellUpdate += new Infragistics.Win.UltraWinGrid.CellEventHandler(this.ugdQCGroup_AfterCellUpdate);
            this.ugdQCGroup.InitializeLayout += new Infragistics.Win.UltraWinGrid.InitializeLayoutEventHandler(this.ugdQCGroup_InitializeLayout);
            this.ugdQCGroup.BeforeCellActivate += new Infragistics.Win.UltraWinGrid.CancelableCellEventHandler(this.ugdQCGroup_BeforeCellActivate);
            this.ugdQCGroup.KeyDown += new System.Windows.Forms.KeyEventHandler(this.ugdQCGroup_KeyDown);
            // 
            // ugbQCGroup
            // 
            this.ugbQCGroup.Anchor = ((System.Windows.Forms.AnchorStyles)((((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom)
                        | System.Windows.Forms.AnchorStyles.Left)
                        | System.Windows.Forms.AnchorStyles.Right)));
            this.ugbQCGroup.Controls.Add(this.ubtnCancel);
            this.ugbQCGroup.Controls.Add(this.ubtnOK);
            this.ugbQCGroup.Controls.Add(this.ugdQCGroup);
            this.ugbQCGroup.Controls.Add(this.ulblQCGroup);
            this.ugbQCGroup.Controls.Add(this.ucmbQCGroup);
            this.ugbQCGroup.Location = new System.Drawing.Point(0, 0);
            this.ugbQCGroup.Name = "ugbQCGroup";
            this.ugbQCGroup.Size = new System.Drawing.Size(775, 230);
            this.ugbQCGroup.TabIndex = 0;
            // 
            // ubtnCancel
            // 
            this.ubtnCancel.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Right)));
            this.ubtnCancel.Location = new System.Drawing.Point(714, 202);
            this.ubtnCancel.Name = "ubtnCancel";
            this.ubtnCancel.Size = new System.Drawing.Size(56, 23);
            this.ubtnCancel.TabIndex = 4;
            this.ubtnCancel.Text = "&Cancel";
            this.ubtnCancel.Click += new System.EventHandler(this.ubtnCancel_Click);
            this.ubtnCancel.KeyDown += new System.Windows.Forms.KeyEventHandler(this.ubtnCancel_KeyDown);
            // 
            // ubtnOK
            // 
            this.ubtnOK.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Right)));
            this.ubtnOK.Location = new System.Drawing.Point(656, 202);
            this.ubtnOK.Name = "ubtnOK";
            this.ubtnOK.Size = new System.Drawing.Size(56, 23);
            this.ubtnOK.TabIndex = 3;
            this.ubtnOK.Text = "&OK";
            this.ubtnOK.Click += new System.EventHandler(this.ubtnOK_Click);
            this.ubtnOK.KeyDown += new System.Windows.Forms.KeyEventHandler(this.ubtnOK_KeyDown);
            // 
            // ucmbQCGroup
            // 
            this.ucmbQCGroup.AutoSize = false;
            this.ucmbQCGroup.Location = new System.Drawing.Point(131, 7);
            this.ucmbQCGroup.Name = "ucmbQCGroup";
            this.ucmbQCGroup.Size = new System.Drawing.Size(200, 20);
            this.ucmbQCGroup.TabIndex = 1;
            this.ucmbQCGroup.ValueChanged += new System.EventHandler(this.ucmbQCGroup_ValueChanged);
            this.ucmbQCGroup.KeyDown += new System.Windows.Forms.KeyEventHandler(this.ucmbQCGroup_KeyDown);
            // 
            // QCGroup
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(7F, 15F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.Controls.Add(this.ugbQCGroup);
            this.Font = new System.Drawing.Font("Microsoft Sans Serif", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.Name = "QCGroup";
            this.Size = new System.Drawing.Size(775, 230);
            this.Load += new System.EventHandler(this.QCGroup_Load);
            ((System.ComponentModel.ISupportInitialize)(this.ugdQCGroup)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.ugbQCGroup)).EndInit();
            this.ugbQCGroup.ResumeLayout(false);
            this.ugbQCGroup.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.ucmbQCGroup)).EndInit();
            this.ResumeLayout(false);

        }

        #endregion

        private Infragistics.Win.Misc.UltraLabel ulblQCGroup;
        private Infragistics.Win.UltraWinGrid.UltraGrid ugdQCGroup;
        private Infragistics.Win.UltraWinGrid.UltraCombo ucmbQCGroup;
        private Infragistics.Win.Misc.UltraGroupBox ugbQCGroup;
        private Infragistics.Win.Misc.UltraButton ubtnCancel;
        private Infragistics.Win.Misc.UltraButton ubtnOK;


    }
}
