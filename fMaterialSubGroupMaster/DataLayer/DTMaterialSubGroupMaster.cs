using System;
using System.Collections.Generic;
using System.Text;
using System.Data;
namespace SpectrumERP.DataLayer
{
    public class DTMaterialSubGroupMaster
    {
        #region private


        private bool bInactive;
        private byte btCompanyNo;
        private byte btWHCompanyNo;
        private byte btDeductionRate;
        private byte btDeductionType;
        private byte btUnitTypeNo;
        private Nullable<double> dDoubleDeductionFrom;
        private double dReceiptTolerance;
        private double dShipmentTolerance;
        private double dStandardValue;
        private double dToleranceValue;
        private Nullable <int> iDivisionNo;
        private int iVendorLocationNo;
        private int iVendorNo;
        private Nullable<short> sCategoryNo;
        private Nullable<short> sGroupNo;
        private short sLoginNo;
        private short sMakeNo;
        private short sQCParameterNo;
        private Nullable <short> sSubGroupNo;
        private string strFullSubGroupCode;
        private string strCode;
        private string strSubGroupName;
        private short sUnitNo;
        private short sWarehouseNo;
        private Nullable<byte> sStockValueMethodNo;
        // 30 may 2017
        private Nullable<byte> btGSTCategoryNo;
        private Nullable<short> sHSNSACCodeNo;
        //16 June 2023
        private short sBinNo;
        //28 June 2023
        private bool bIsBINApplicable;
        private Nullable<double> dDispatchNegTolerance;
        
        #endregion


        # region public
        public Nullable<short> HSNSACCodeNo
        {
            get { return sHSNSACCodeNo; }
            set { sHSNSACCodeNo = value; }
        }
        public Nullable<byte> GSTCategoryNo
        {
            get { return btGSTCategoryNo; }
            set { btGSTCategoryNo = value; }
        }
        public Nullable<byte> StockValueMethodNo
        {
            get { return sStockValueMethodNo; }
            set { sStockValueMethodNo = value; }
        }

        public bool Inactive
        {
            get { return bInactive; }
            set { bInactive = value; }
        }
        public byte CompanyNo
        {
            get { return btCompanyNo; }
            set { btCompanyNo = value; }
        }
        public byte WHCompanyNo
        {
            get { return btWHCompanyNo; }
            set { btWHCompanyNo = value; }
        }
        public byte DeductionRate
        {
            get { return btDeductionRate; }
            set { btDeductionRate = value; }
        }
        public byte DeductionType
        {
            get { return btDeductionType; }
            set { btDeductionType = value; }
        }
        public byte UnitTypeNo
        {
            get { return btUnitTypeNo; }
            set { btUnitTypeNo = value; }
        }
        public Nullable<double> DoubleDeductionFrom
        {
            get { return dDoubleDeductionFrom; }
            set { dDoubleDeductionFrom = value; }
        }
        public double ReceiptTolerance
        {
            get { return dReceiptTolerance; }
            set { dReceiptTolerance = value; }
        }
        public double ShipmentTolerance
        {
            get { return dShipmentTolerance; }
            set { dShipmentTolerance = value; }
        }
        public double StandardValue
        {
            get { return dStandardValue; }
            set { dStandardValue = value; }
        }
        public double ToleranceValue
        {
            get { return dToleranceValue; }
            set { dToleranceValue = value; }
        }
        public Nullable <int> DivisionNo
        {
            get { return iDivisionNo; }
            set { iDivisionNo = value; }
        }
        public int VendorLocationNo
        {
            get { return iVendorLocationNo; }
            set { iVendorLocationNo = value; }
        }
        public int VendorNo
        {
            get { return iVendorNo; }
            set { iVendorNo = value; }
        }
        public Nullable<short> CategoryNo
        {
            get { return sCategoryNo; }
            set { sCategoryNo = value; }
        }
        public Nullable<short> GroupNo
        {
            get { return sGroupNo; }
            set { sGroupNo = value; }
        }
        public short LoginNo
        {
            get { return sLoginNo; }
            set { sLoginNo = value; }
        }
        public short MakeNo
        {
            get { return sMakeNo; }
            set { sMakeNo = value; }
        }
        public short QCParameterNo
        {
            get { return sQCParameterNo; }
            set { sQCParameterNo = value; }
        }
        public Nullable<short> SubGroupNo
        {
            get { return sSubGroupNo; }
            set { sSubGroupNo = value; }
        }

        public short WarehouseNo
        {
            get { return sWarehouseNo; }
            set { sWarehouseNo = value; }
        }

        public string FullSubGroupCode
        {
            get { return strFullSubGroupCode; }
            set { strFullSubGroupCode = value; }
        }
        public string Code
        {
            get { return strCode; }
            set { strCode = value; }
        }
        public string SubGroupName
        {
            get { return strSubGroupName; }
            set { strSubGroupName = value; }
        }
        public short UnitNo
        {
            get { return sUnitNo; }
            set { sUnitNo = value; }
        }
        public short BinNo
        {
            get { return sBinNo; }
            set { sBinNo = value; }
        }
        public bool IsBINApplicable
        {
            get { return bIsBINApplicable; }
            set { bIsBINApplicable = value; }
        }

        public Nullable<double> DispatchNegTolerance
        {
            get { return dDispatchNegTolerance; }
            set { dDispatchNegTolerance = value; }
        }

        #endregion


        public DataSet FillValuesDependent()
        {
            DAMaterialSubGroupMaster objDAMaterialSubGroupMaster = new DAMaterialSubGroupMaster();
            return objDAMaterialSubGroupMaster.FillValuesDependent(this);
        }


        public DataSet Validate()
        {
            DAMaterialSubGroupMaster objDAMaterialSubGroupMaster = new DAMaterialSubGroupMaster();
            return objDAMaterialSubGroupMaster.Validate(this);
        }


        public DataSet SaveDivision()
        {
            DAMaterialSubGroupMaster objDAMaterialSubGroupMaster = new DAMaterialSubGroupMaster();
            return objDAMaterialSubGroupMaster.SaveDivision(this);
        }


        public DataSet SaveMake()
        {
            DAMaterialSubGroupMaster objDAMaterialSubGroupMaster = new DAMaterialSubGroupMaster();
            return objDAMaterialSubGroupMaster.SaveMake(this);
        }


        public DataSet SaveQC()
        {
            DAMaterialSubGroupMaster objDAMaterialSubGroupMaster = new DAMaterialSubGroupMaster();
            return objDAMaterialSubGroupMaster.SaveQC(this);
        }


        public DataSet SaveUnit()
        {
            DAMaterialSubGroupMaster objDAMaterialSubGroupMaster = new DAMaterialSubGroupMaster();
            return objDAMaterialSubGroupMaster.SaveUnit(this);
        }


        public DataSet SaveVendor()
        {
            DAMaterialSubGroupMaster objDAMaterialSubGroupMaster = new DAMaterialSubGroupMaster();
            return objDAMaterialSubGroupMaster.SaveVendor(this);
        }


        public DataSet SaveMain()
        {
            DAMaterialSubGroupMaster objDAMaterialSubGroupMaster = new DAMaterialSubGroupMaster();
            return objDAMaterialSubGroupMaster.SaveMain(this);
        }


        public DataSet Delete()
        {
            DAMaterialSubGroupMaster objDAMaterialSubGroupMaster = new DAMaterialSubGroupMaster();
            return objDAMaterialSubGroupMaster.Delete(this);
        }


        public DataSet SearchData()
        {
            DAMaterialSubGroupMaster objDAMaterialSubGroupMaster = new DAMaterialSubGroupMaster();
            return objDAMaterialSubGroupMaster.SearchData(this);
        }


        public DataSet LoadData()
        {
            DAMaterialSubGroupMaster objDAMaterialSubGroupMaster = new DAMaterialSubGroupMaster();
            return objDAMaterialSubGroupMaster.LoadData(this);
        }


        public DataSet FillValues()
        {
            DAMaterialSubGroupMaster objDAMaterialSubGroupMaster = new DAMaterialSubGroupMaster();
            return objDAMaterialSubGroupMaster.FillValues(this);
        }


        public DataSet SaveBinDetail()
        {
            DAMaterialSubGroupMaster objDAMaterialSubGroupMaster = new DAMaterialSubGroupMaster();
            return objDAMaterialSubGroupMaster.SaveBinDetail(this);
        }
    }
}
