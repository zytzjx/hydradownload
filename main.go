package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"strconv"

	cmc "github.com/zytzjx/anthenacmc/cmcserverinfo"
	"github.com/zytzjx/anthenacmc/cmcupdate"
	Log "github.com/zytzjx/anthenacmc/loggersys"
	_ "github.com/zytzjx/anthenacmc/loggersys"
	"github.com/zytzjx/anthenacmc/utils"
)

// CreateClientStatus for next
func CreateClientStatus() error {
	var cliinfo cmcupdate.ClientInfo

	jsonFile, err := os.Open("serialconfig.json")
	// if we os.Open returns an error then handle it
	if err != nil {
		Log.Log.Error(err)
		return fmt.Errorf("serial number run first. %s", err)
	}
	fmt.Println("Successfully Opened serialconfig.json")
	// defer the closing of our jsonFile so that we can parse it later on
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	var dat cmc.ConfigInstall //map[string]interface{}
	if err := json.Unmarshal(byteValue, &dat); err != nil {
		// panic(err)
		return err
	}
	cliinfo.Company, _ = dat.Results[0].GetCompanyID()
	cliinfo.Productid, _ = strconv.Atoi(dat.Results[0].Productid)
	cliinfo.Solutionid, _ = strconv.Atoi(dat.Results[0].Solutionid)

	jsonFile, err = os.Open("updatelist.json")
	// if we os.Open returns an error then handle it
	if err != nil {
		Log.Log.Error(err)
		return err
	}
	// defer the closing of our jsonFile so that we can parse it later on
	defer jsonFile.Close()
	var download cmcupdate.StatusResponse
	byteValue, _ = ioutil.ReadAll(jsonFile)
	if err = json.Unmarshal(byteValue, &download); err != nil {
		os.Exit(8)
	}

	sync := cmcupdate.SyncStatus{}

	if utils.FileExists("clientstatus.json") {
		jsonFile, err = os.Open("clientstatus.json")
		// if we os.Open returns an error then handle it
		if err != nil {
			Log.Log.Error(err)
			return err
		}
		// defer the closing of our jsonFile so that we can parse it later on
		defer jsonFile.Close()

		byteValue, _ = ioutil.ReadAll(jsonFile)
		if err = json.Unmarshal(byteValue, &sync); err != nil {
			Log.Log.Error(err)
		}
	} else {
		sync.Protocol = "2.0"
		sync.Client = cliinfo
	}

	sync.Sync.Status.Framework.Filelist = make([]map[string]interface{}, 0)
	if download.Framework.Version != "" {
		sync.Sync.Status.Framework.Version = download.Framework.Version
	}
	sync.Sync.Status.Phonedll.Deletelist = make([]map[string]interface{}, 0)
	sync.Sync.Status.Phonedll.Filelist = download.Phonedll.Filelist
	sync.Sync.Status.Phonetips.Deletelist = make([]map[string]interface{}, 0)
	sync.Sync.Status.Phonetips.Filelist = download.Phonetips.Filelist

	for i, v := range sync.Sync.Status.Phonedll.Filelist {
		delete(v, "url")
		sync.Sync.Status.Phonedll.Filelist[i] = v
	}
	for i, v := range sync.Sync.Status.Phonetips.Filelist {
		delete(v, "url")
		sync.Sync.Status.Phonedll.Filelist[i] = v
	}

	file, _ := json.MarshalIndent(sync, "", " ")

	_ = ioutil.WriteFile("clientstatus.json", file, 0644)

	return nil
}

func main() {
	Log.NewLogger("updatecmc")
	faillist, err := cmcupdate.DownloadCMC()
	if err != nil {
		_, err = cmcupdate.RetryDownload(faillist)
	}
	if err != nil {
		os.Exit(1)
	}
	if CreateClientStatus() != nil {
		os.Exit(8)
	}
	os.Exit(0)
}
